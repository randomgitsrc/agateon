#!/usr/bin/env python3
"""agate-feedback.py — agate 跨项目反馈提取（AG0021，TAG0015 新增）

从一份复盘文档（retrospective.md，见 agate/assets/templates/retrospective-template.md）
提取 frontmatter 机器字段（mechanism_issues/execution_issues/feedback_ready）与
「## agate 反馈」结构化节内容，做轻量脱敏（项目名占位符化 + 绝对路径截断/移除），
输出结构化 JSON + 面向 issue/PR 的 Markdown 文本片段，供人工手动提交。

**手动触发，不存在任何自动触发该脚本的钩子/CI/定时任务**（BDD-20）。
本脚本只产出待人工提交的内容，不执行任何网络提交动作——不调用任何外部版本控制/
代码托管命令，不做任何形式的自动网络提交。

AGATE_FEEDBACK 开关默认 off（opt-in），沿用仓库既有 os.environ.get("AGATE_XXX", 默认值)
惯例（参照 agate_common.py 的 AGATE_TDD_TIMEOUT 读取模式）。
"""

import argparse
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("agate-feedback: 需要 pyyaml。pip install pyyaml\n")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MD_FIELD_GET = os.path.join(SCRIPT_DIR, "agate-md-field-get.py")

AGATE_FEEDBACK_SECTION_RE = re.compile(r"^## agate 反馈\s*$", re.MULTILINE)
NEXT_HEADING_RE = re.compile(r"^## ", re.MULTILINE)
# 绝对路径匹配：类 Unix 与类 Windows 连续 token（P2-design.md §2 候选方案 B1）。
# RM-AG0082 / DEBT0008：原正则 `(?:[A-Za-z]:\\|/)[^\s'"`]+` 把**任何以 / 开头的
# 子串**都当绝对路径，中文散文里的斜杠分隔词被误伤（`机制/执行层面` → `/执行层面`）。
# 现收窄为"真的像绝对路径"的形态，满足其一即可：
#   1. Windows 盘符 `C:\...`（保持现状）；
#   2. Unix 已知顶层目录 `/home/ /Users/ /tmp/ /var/ /etc/ /opt/ /root/ /mnt/
#      /srv/ /usr/` 开头且至少含 2 段；
#   3. 以 `/` 开头且至少含 3 段（`/a/b/c` 形态）。
# 取舍：匿名化是隐私功能，宁可多留不可漏——故不额外加"斜杠前须是边界"的负向断言
# （那会漏掉紧贴中文/标点的真实路径）。判据 3 改用「**首段为 ASCII 路径段**」——
# 既排除中文斜杠词（`机制/执行层面`、`机制/执行/流程/层面`：首段为 CJK ⇒ 不匹配），
# 又不漏真实路径（`/data/secret`、`/proj/foo`：首段为 ASCII ⇒ 匹配）。
# **已知残留漏脱敏面**（SELF-GATE 评审如实登记，取舍在"更宽"侧之外）：
#   * **首段为 CJK 的真实路径**（如 `/项目/secret`）不匹配 ⇒ 不脱敏；
#   * **单段绝对路径**（如 `/data`、`/secret`）不匹配 ⇒ 不脱敏（1 段无法与斜杠词区分）。
#   二者均属罕见形态；如需覆盖，应在**消费方**用更精确的来源（如已知路径前缀）判定，
#   而非继续放宽本正则（放宽会把中文斜杠词重新误伤）。
ABS_PATH_RE = re.compile(
    r"(?:"
    r"[A-Za-z]:\\[^\s'\"`]+"  # 1. Windows 盘符路径
    r"|/(?:home|Users|tmp|var|etc|opt|root|mnt|srv|usr)/[^\s'\"`]+"  # 2. Unix 已知顶层目录（≥2 段）
    r"|/[A-Za-z0-9._-]+/[^\s'\"`]+"  # 3. 通用：/ 开头、首段为 ASCII 路径段、≥2 段
    r")"
)

DISABLED_MESSAGE = "agate-feedback: 功能未启用（设置 AGATE_FEEDBACK=on 启用）\n"

# 由 main() 在解析参数后写入，供 _anonymize() 读取（保持 _anonymize(text, project_root)
# 两参数签名与 P2-design.md §2 候选方案 B1 一致，项目名通过模块级可变容器传入，
# 避免用 global 语句重绑定模块变量——只做 dict 内容更新，不触发 ruff PLW0603）。
_STATE = {"project_name": ""}


def _md_field_get(op, file_path):
    """调 agate-md-field-get.py op（env FILE），失败回退 ""。

    ADR-007 单一双读工具（重试#1 A7 修复）：mechanism_issues/execution_issues/
    feedback_ready 三字段改为调用该工具读取，不再本地重新实现 frontmatter 字段解析。
    模式参照 agate/scripts/check-gate.py:_md_field_get。
    """
    env = dict(os.environ)
    env["FILE"] = file_path
    try:
        proc = subprocess.run(
            [sys.executable, MD_FIELD_GET, op],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").rstrip("\n")


def _extract_frontmatter_block(text):
    """只认文件头 --- 块；无块（或未闭合）返回 None。

    参照 agate-frontmatter-check.py:128-136 的 _extract_frontmatter_block 正则模式，
    本地实现一份等价函数（不 import 该脚本）。
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    return text[4:end]


def _extract_agate_feedback_section(text):
    """定位「## agate 反馈」小节，取到下一个 `## ` 标题或文件尾为止的节内文本。"""
    m = AGATE_FEEDBACK_SECTION_RE.search(text)
    if not m:
        return ""
    start = m.end()
    next_m = NEXT_HEADING_RE.search(text, start)
    section = text[start:next_m.start()] if next_m else text[start:]
    return section.strip()


def _anonymize(text, project_root):
    """轻量正则脱敏：先做绝对路径处理，再做项目名替换（P2-design.md §2 候选方案 B1）。

    顺序理由：路径规则优先命中并整体替换/截断，避免路径里恰好包含项目名字符串时
    被两条规则重复处理——截断后的相对路径部分不再二次做项目名替换。
    """
    if not text:
        return text

    norm_root = project_root.rstrip(os.sep) if project_root else ""

    def _replace_path(match):
        raw = match.group(0)
        if norm_root and (raw == norm_root or raw.startswith(norm_root + os.sep)):
            rel = raw[len(norm_root):].lstrip(os.sep)
            return rel if rel else "."
        return "<PATH>"

    result = ABS_PATH_RE.sub(_replace_path, text)

    project_name = _STATE["project_name"]
    if project_name:
        name_re = re.compile(r"\b" + re.escape(project_name) + r"\b", re.IGNORECASE)
        result = name_re.sub("<PROJECT>", result)

    return result


def _build_markdown(payload):
    lines = ["# agate 反馈草稿（待人工提交）", ""]
    lines.append("## 机制缺口")
    if payload["mechanism_issues"]:
        for item in payload["mechanism_issues"]:
            lines.append(f"- {item}")
    else:
        lines.append("（无）")
    lines.append("")
    lines.append("## 执行错误")
    if payload["execution_issues"]:
        for item in payload["execution_issues"]:
            lines.append(f"- {item}")
    else:
        lines.append("（无）")
    lines.append("")
    lines.append("## 详情（「## agate 反馈」节内容，已脱敏）")
    lines.append(payload["agate_feedback_section"] or "（无）")
    lines.append("")
    lines.append("---")
    lines.append("请提交前人工复核以下内容是否包含未预期的项目特定信息")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="从复盘文档提取并脱敏「## agate 反馈」内容，产出待人工提交的 JSON/Markdown"
    )
    parser.add_argument("retro_path", help="复盘文档路径（retrospective.md）")
    parser.add_argument(
        "--project-name",
        default=None,
        help="项目名（未提供时默认取 os.path.basename(os.getcwd())）",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="输出格式，默认 both（同时打印 JSON 与 Markdown，用分隔行区分）",
    )
    args = parser.parse_args()

    if os.environ.get("AGATE_FEEDBACK", "off") != "on":
        sys.stderr.write(DISABLED_MESSAGE)
        sys.exit(2)

    project_root = os.getcwd()
    _STATE["project_name"] = args.project_name or os.path.basename(project_root)

    if not os.path.isfile(args.retro_path):
        sys.stderr.write(f"agate-feedback: 文件不存在: {args.retro_path}\n")
        sys.exit(1)

    with open(args.retro_path, encoding="utf-8") as f:
        text = f.read()

    fm_block = _extract_frontmatter_block(text)
    if fm_block is None:
        sys.stderr.write("agate-feedback: 未找到 frontmatter 块（文件头 --- ... ---）\n")
        sys.exit(1)

    try:
        fm_data = yaml.safe_load(fm_block) or {}
    except yaml.YAMLError as exc:
        sys.stderr.write(f"agate-feedback: frontmatter 解析失败: {exc}\n")
        sys.exit(1)

    # ADR-007 单一双读工具（重试#1 A7 修复）：三字段改由 agate-md-field-get.py 统一读取，
    # 不再本地重新实现 frontmatter 字段解析（NO_FALLBACK_LIST_FIELDS/NO_FALLBACK_BOOL_FIELDS，
    # 见 agate-md-field-get.py 对应注册）。
    mechanism_issues_raw = _md_field_get("mechanism_issues", args.retro_path)
    execution_issues_raw = _md_field_get("execution_issues", args.retro_path)
    mechanism_issues = mechanism_issues_raw.split("\n") if mechanism_issues_raw else []
    execution_issues = execution_issues_raw.split("\n") if execution_issues_raw else []
    feedback_ready = _md_field_get("feedback_ready", args.retro_path) == "true"

    section_text = _extract_agate_feedback_section(text)

    payload = {
        "task_id": fm_data.get("task_id", ""),
        "feedback_ready": feedback_ready,
        "mechanism_issues": [_anonymize(str(i), project_root) for i in mechanism_issues],
        "execution_issues": [_anonymize(str(i), project_root) for i in execution_issues],
        "agate_feedback_section": _anonymize(section_text, project_root),
    }

    outputs = []
    if args.format in ("json", "both"):
        outputs.append(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.format in ("markdown", "both"):
        outputs.append(_build_markdown(payload))

    print("\n\n---\n\n".join(outputs))
    sys.exit(0)


if __name__ == "__main__":
    main()
