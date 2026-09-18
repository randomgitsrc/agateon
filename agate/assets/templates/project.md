# project.md 模板

> 复制此文件到 `{AGATE_WORKSPACE}/agents/project.md`，按需填写后删掉本说明块。
> **这个文件是可选的**——orchestrator 默认只读 `AGENTS.md`/`CLAUDE.md`；如果你的项目没有"只有编排任务时才用得上、放进通用开发指引会显得突兀"的操作细节，不需要创建这个文件，跳过即可。
> 反过来，如果有（比如多工作区隔离规则、专属 gate 命令、测试基线数字这类），才建这个文件——它是 orchestrator 专属的操作性事实来源，和面向所有贡献者的 AGENTS.md 分开，避免互相污染。
> `orchestrator-template.md` 本身对所有项目内容完全一致（通常是符号链接，不是拷贝），**这个文件才是你唯一应该编辑的地方**。

---

<!--
以下字段和小节都是可选的，按需保留/删除，没有固定 schema——orchestrator 会整份读取理解，不依赖机器解析特定字段名。
-->

## agate_root / project_root 覆盖（大多数项目不需要，删掉这节即可）

如果你的 agate 没装在默认位置 `~/.agate`（TAG0008 起也可为版本管理根目录——项目经 `.agate-version` 解析到 `~/.agate/vX.Y.Z/`，此时 orchestrator 自动解析无需覆盖；若需要显式指定可用 AGATE_ROOT env；只想换"版本根在哪"（如多套版本根并存）用 AGATE_HOME env），或者 `project_root` 不能用"向上找最近的 `.git` 目录"这条默认规则正确推出来（比如 monorepo 里想显式指定某个子目录为 project_root），在这里声明：

```
agate_root: /path/to/your/agate-clone/agate
project_root: /absolute/path/to/this/project
```

## 工作区/环境约束（如果适用）

<!-- 例：多工作区隔离规则（改造对象 vs 开发工具分离）、禁止改动的路径、必须使用的软链接等。 -->

## Gate / 测试命令

<!-- 例：本项目的 gate_commands 覆盖点、测试基线数字（不能漂移的用例总数）、shellcheck/lint 命令。 -->

## 发布约定

<!-- 例：版本号规则、tag 格式、merge 方式（--no-ff / squash）、CHANGELOG 位置（若非仓库根 CHANGELOG.md）。 -->

## 其他 orchestrator 需要知道但不适合写进 AGENTS.md 的事

<!-- 任何一次性的、任务期特有的、或者纯粹"编排层"才关心的约束都放这里。 -->
