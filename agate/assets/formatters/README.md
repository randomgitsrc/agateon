# Test Output Formatter Contract

agate 协议通过 **formatter 适配层**实现技术栈无关的测试输出解析。每个 formatter 将特定测试运行器的原始输出转换为统一 JSON 格式，供 `check-tdd-red.py` 等 gate 脚本消费。

## 契约

| 项目 | 说明 |
|------|------|
| **输入** | stdin = 测试原始输出（stdout+stderr 合并）；`$1` = 测试运行器 exit code |
| **输出** | stdout = 一行 JSON（紧凑格式，末尾换行） |
| **退出码** | `0` = 解析成功；`1` = 解析失败（formatter 自身出错） |

## 标准 JSON 格式

```json
{
  "exit_code": 1,
  "total": 7,
  "passed": 5,
  "failed": 2,
  "errors": 0,
  "failed_tests": ["tests/test_a.py::test_one", "tests/test_b.py::test_two"],
  "import_errors": [
    {"module": "myapp.foo", "message": "cannot import name 'Bar' from 'myapp.foo'"}
  ],
  "syntax_errors": [
    {"file": "tests/test_x.py", "message": "SyntaxError: invalid syntax"}
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `exit_code` | `int` | 测试运行器原始退出码（`$1` 传入） |
| `total` | `int` | 测试总数（passed + failed + errors）。formatter 无法从输出中提取时为 `0` |
| `passed` | `int` | 通过的测试数 |
| `failed` | `int` | assertion 失败的测试数 |
| `errors` | `int` | collection/fixture/setup 错误数（非 assertion 失败） |
| `failed_tests` | `string[]` | 失败测试的标识符（文件路径、测试名等） |
| `import_errors` | `object[]` | import/依赖缺失错误，每项含 `module`（缺失模块名）和 `message`（原始错误行） |
| `syntax_errors` | `object[]` | 语法/编译错误，每项含 `file`（文件路径，可为空字符串）和 `message`（原始错误行） |

## 速查表

| 测试运行器 | formatter | 备注 |
|-----------|-----------|------|
| pytest | `pytest.sh` | Python 标准格式 |
| vitest / jest | `vitest.sh` | JS/TS 生态 |
| go test | `go-test.sh` | Go 原生 + cargo test 共用 |
| cargo test | `go-test.sh` | Rust，输出格式与 go test 相似 |
| bats | `generic-tap.sh` | TAP 协议格式 |
| Maven / Gradle | `generic-junit-xml.sh` | JUnit XML surefire 报告 |
| 其他 | `generic-exit-only.sh` | 退路：只用 exit code，不解析输出 |

## gate_commands 声明

在 `P2-design.md` 的 `gate_commands` 中声明 formatter：

```yaml
gate_commands:
  P3: "pytest -q"
  P3_formatter: "pytest.sh"
  P5: "pytest -q --tb=no"
  P5_formatter: "pytest.sh"
  project_module: "myapp"
```

| 键 | 说明 |
|----|------|
| `P3_formatter` / `P5_formatter` | formatter 脚本路径或名称 |
| `project_module` | 项目模块前缀，用于 B 类检测（区分项目内 import vs 第三方 import） |

未声明 `P3_formatter` 时，gate 脚本回退到 `generic-exit-only.sh`。

## formatter 路径解析规则

```
1. 绝对路径（以 / 开头）→ 直接使用
2. 相对路径/纯文件名：
   a. 先找 .agate/formatters/<name>（项目自定义）
   b. 再找 {agate_root}/assets/formatters/<name>（内置）
3. 找不到 → 回退 generic-exit-only.sh
```

项目可在 `.agate/formatters/` 放自定义 formatter 覆盖内置版本。

## 多技术栈声明

多语言项目仍使用单栈精确 `P3` 声明检测命令（历史 `P3_js` / `P3_html` 形态已退役，解析器丢弃未登记后缀）：

```yaml
gate_commands:
  P3: "pytest -q"
  P3_formatter: "pytest.sh"
  project_module: "myapp"
```

`P3` / `P3_formatter` / `project_module` 为当前唯一有效的检测键组合；未来多栈并行需先经协议修订登记收集后缀，未登记的后缀键不被收集执行。

## 自定义 formatter

编写自定义 formatter 只需遵循上述契约：

1. 创建脚本（如 `.agate/formatters/my-runner.sh`）
2. 从 stdin 读原始输出，从 `$1` 读 exit code
3. 输出一行标准 JSON
4. 退出码 0（成功）或 1（解析失败）

内置 formatter 均使用内联 python3 解析，可作为参考实现。

### ⚠️ 两个必看的实现陷阱（`TAG0039` 实测，两者都曾造成静默故障）

**① 不要把整份输出经环境变量传给 `python3`。** 常见写法 `OUTPUT="$(cat)"; export OUTPUT` 在输出超过 execve 的 `MAX_ARG_STRLEN`（128 KB，见 `getconf ARG_MAX` 相关限制）时会让 `python3` **启动即失败**（`参数列表过长`，退出码 126）。真实规模：某前端项目全量输出约 1.5 MB，超限 11 倍 → formatter 失败 → 上游 `check-tdd-red.py` 回退 `raw_output` 并**误判为红灯**，`ci-gate-backstop.py` 据此判 **FAIL**。

正确做法是经**临时文件**传递（内置 formatter 现在都是这个写法）：

```bash
TMP="$(mktemp)"; trap 'rm -f "$TMP"' EXIT
cat > "$TMP"
python3 - "$TMP" <<'PYEOF'
import sys
with open(sys.argv[1], "r", encoding="utf-8", errors="replace") as fh:
    output = fh.read()
...
PYEOF
```

（若 formatter **不需要**输出，就别读它——`cat > /dev/null` 排空 stdin 即可；多余的 `export` 同样会让 `python3` 因 E2BIG 启动失败。）

**② 别用 `.*(?:关键字).*` 这类前置 `.*` 正则在整份输出上搜。** `.` 不跨 `\n`，所以它等价于"整行匹配"，但在**超长单行**上会退化为 **O(n²)**：实测 32 KB 单行 2.1 s、尺寸翻倍耗时 ×4，1.8 MB 单行外推约 **1.8 小时**——而且**恰恰是"没有命中"的正常路径最慢**（找到就提前返回）。`run_test_with_formatter` 对 formatter 设了有界超时（`AGATE_FORMATTER_TIMEOUT`，默认 120 s），超时会降级为原始输出，但那是兜底、不是许可。

改成**逐行扫描**即线性（`.` 本就不跨 `\n`，故扫描面与旧式一致）：

> **⚠️ 取「首个」还是「末个」匹配会改变结果**：旧式 `.*(?:关键字).*` 的 `.*` 会**回溯到末个起点**，
> 所以捕获组取的是**最后一个**匹配；逐行改写若顺手用 `re.search`（取**首个**）就是**语义变化**，
> 不是等价替换（`TAG0039` 独立评审的实测反例：单行含两个 `NameError` 时，`symbol` 由
> `myapp.a` 变成 `x`）。有捕获组时须显式取末个：`list(re.finditer(pat, raw))[-1]`。
> 只取整行（`m.group(0).strip()`、无捕获组）时首个/末个都产出同一行，不受此影响。

```python
for raw in output.split("\n"):
    if "关键字" not in raw:
        continue
    line = raw.strip()   # 无捕获组时与旧 `m.group(0).strip()` 等价（见上方取首个/末个说明）
```

## 内置 formatter 清单

| 脚本 | 解析策略 |
|------|---------|
| `generic-exit-only.sh` | 不解析输出，仅用 exit code 填 `exit_code`，其余字段归零 |
| `pytest.sh` | 正则提取 `N passed/failed/error` + `FAILED` 行 + ImportError/SyntaxError |
| `vitest.sh` | 正则提取 `Tests N failed/passed` + `Failed Suites` + `Cannot find module` |
| `go-test.sh` | 正则提取 `N passed/failed` + `--- FAIL:` / `test ... FAILED` + import/syntax error |
| `generic-tap.sh` | 统计 `^ok` / `^not ok` 行 |
| `generic-junit-xml.sh` | 从 XML 属性提取 `tests/failures/errors` |
