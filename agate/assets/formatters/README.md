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
| pytest | `pytest.sh` | Python 标准格式 | `pyt.py` |
| vitest / jest | `vitest.sh` | JS/TS 生态 | `vit.py` |
| go test | `go-test.sh` | Go 原生 + cargo test 共用 | `go-t.py` |
| cargo test | `go-test.sh` | Rust，输出格式与 go test 相似 | `go-t.py` |
| bats | `generic-tap.sh` | TAP 协议格式 | `generic-.py` |
| Maven / Gradle | `generic-junit-xml.sh` | JUnit XML surefire 报告 | `generic-junit-.py` |
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

**① 不要把整份输出经环境变量传给 `python3`。** 常见写法 `OUTPUT="$(cat)"; export OUTPUT` 在输出超过 execve 的 `MAX_ARG_STRLEN`（128 KB，见 `getconf ARG_MAX` 相关限制）时会让 `python3` **启动即失败**（`参数列表过长`，退出码 126）。真实规模：某前端项目全量输出约 1.5 MB，超限 11 倍 → formatter 失败 → 上游 `check-tdd-red.py` 回退 `raw_output` 并**误判为红灯**，CI 兜底据此判 **FAIL**。

正确做法：**bash 薄壳 + 独立 `.py`，数据经 stdin 直连**（内置 formatter 现在都是这个结构）：

```bash
# vitest.sh —— 薄壳
#!/usr/bin/env bash
set -euo pipefail
exec python3 "$(dirname "$0")/vitest.py" "${1:-1}"
```

```python
# vitest.py —— 解析实现
import sys
output = sys.stdin.read()      # 数据走 stdin，不经 argv/env/临时文件
exit_code = int(sys.argv[1]) if len(sys.argv) > 1 else 1
```

> **为什么是"独立 .py"而不是其他写法**（`TAG0039` 三条路都试过，全部失败，勿重蹈）：
>
> | 写法 | 失败原因 |
> |---|---|
> | 输出经**环境变量**传 | 超 `MAX_ARG_STRLEN`(128 KB) → python3 启动即 E2BIG（**本缺陷本身**） |
> | 输出经**临时文件**（`mktemp`） | **新增 TMPDIR 可写依赖**：只读 `/tmp` 下创建失败 + `set -e` → formatter 中止 → 上游回退 `raw_output` → **复活上面的误判路径**（受限沙箱实存） |
> | 脚本经 **fd 3 重定向**（`3<&0` + `os.fdopen(3)`） | Linux 可行，**Windows 上抛 `OSError: [WinError 6] The handle is invalid`**（CI windows-latest 实测；Git Bash 的 fd 重定向不透传给原生 python.exe） |
> | 脚本经 **`-c` + 命令替换** | Windows 下 MSYS2 的 argv 转换对脚本内正则的反斜杠（`\S`/`\.`）敏感 |
>
> 独立 `.py` 走的是 `python3 <file>` + stdin —— 三平台零特殊机制。

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

**入口一律是 `.sh`**（调用契约 `<name>.sh <exit_code>` + stdin 不变）；除 `generic-exit-only.sh`（只回传 exit code、内联即可）外，其余 5 个的解析实现在**同名 `.py`**（如 `vitest.sh` → `vitest.py`，见上方「实现陷阱」的选型理由）。

| 入口 | 解析策略 | 实现 |
|------|---------|------|
| `generic-exit-only.sh` | 不解析输出，仅用 exit code 填 `exit_code`，其余字段归零 | 内联（不读 stdin） |
| `pytest.sh` | 正则提取 `N passed/failed/error` + `FAILED` 行 + ImportError/SyntaxError | `pytest.py` |
| `vitest.sh` | 正则提取 `Tests N failed/passed` + `Failed Suites` + `Cannot find module` | `vitest.py` |
| `go-test.sh` | 正则提取 `N passed/failed` + `--- FAIL:` / `test ... FAILED` + import/syntax error | `go-test.py` |
| `generic-tap.sh` | 统计 `^ok` / `^not ok` 行 | `generic-tap.py` |
| `generic-junit-xml.sh` | 从 XML 属性提取 `tests/failures/errors` | `generic-junit-xml.py` |
