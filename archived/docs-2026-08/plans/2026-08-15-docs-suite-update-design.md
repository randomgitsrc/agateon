# 设计：agate 文档体系更新（README + 入口层 + 引用同步）

日期：2026-08-15
状态：已批准（用户确认范围 + "不对的内容该改也要改掉"原则）

## 背景

v0.46.0（产品逻辑 Python 化）+ v0.47.0（测试框架 bats→pytest）后，文档体系存在过时引用（`install-hook.sh` 应为 `install-hook.py`、`check-gate.sh` 应为 `check-gate.py` 等）与定位问题（README 中英混杂、门面与手册不分）。用户要求整套面向使用者的文档更新，并做独立评审。

## 受众与目标

| 文件 | 受众 | 目标 |
|------|------|------|
| README.md（英文） | GitHub 访客/潜在采用者 | 2 分钟理解 agate 是什么、为什么值得用、怎么开始；门面 + 导航，不承载接入细节 |
| README.zh-CN.md（中文） | 中文用户 | 英文版完整镜像，语言切换链接互通 |
| agate/AGENTS.md | 使用者（人类 + Agent） | 协议本体入口索引：这是什么、怎么用、文档导航、升级/卸载 |
| SETUP/UPGRADING/platform-notes/LIMITATIONS/CONTEXT | 对应场景用户 | 信息准确（py 化/pytest 后的当前状态），无过时引用 |
| 协议文档（role-system/loop/WORKFLOW/adr） | 协议读者 | 当前操作引用改 py；历史记录如有误导性引用也改 |

## 范围

### 第一级：重写
1. `README.md` → 英文门面（结构：tagline → What/Why → Quick start → How it works → Platforms → Documentation → Principles → Limitations → Contributing）
2. `README.zh-CN.md` → 新增中文镜像
3. `agate/AGENTS.md` → 重写入口索引 + 修 `install-hook.sh`→`install-hook.py`

### 第二级：核对更新
4. `agate/SETUP.md`：pyyaml 强制、install-hook.py、pytest 命令
5. `agate/UPGRADING.md`：章节完整性 + 残留引用（迁移对照表保留，非对照错误改）
6. `agate/platform-notes.md`：py 化 Windows 说明 + pytest marker
7. `agate/LIMITATIONS.md`：pyyaml 强制依赖
8. `agate/CONTEXT.md`：术语表 check-gate.sh → py

### 第三级：引用修复
9. `agate/role-system.md` / `agate/loop-orchestration.md` / `agate/WORKFLOW.md`（非 hook py 化引用）+ `agate/adr.md`（历史记录中误导性引用更新，hook 薄壳 pre-commit-gate.sh 保留）

## 关键决策

- **语言**：README 英文默认 + README.zh-CN.md 中文镜像（方案 A）
- **定位**：README 门面型（方案 A）——接入细节归 SETUP.md
- **信息准确性优先**：一切过时引用（即使历史记录）该改则改；hook 薄壳（pre-commit-gate.sh / commit-msg-self-gate.sh / pre-push-gate.sh）保留 sh 是正确状态，不改
- **迁移对照表**（UPGRADING 旧→新命令对照）是讲迁移本身，写旧名正确，保留
- **独立评审**：全部完成后派独立评审角色复核信息准确性/专业性/实践符合度

## 实现批次

1. README.md 英文重写
2. README.zh-CN.md 中文镜像
3. agate/AGENTS.md 重写
4. 第二级核对（SETUP/UPGRADING/platform-notes/LIMITATIONS/CONTEXT）
5. 第三级引用修复（role-system/loop/WORKFLOW/adr）
6. 独立评审 + 修订
