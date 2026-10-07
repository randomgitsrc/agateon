#!/usr/bin/env python3
"""校验 .state.yaml 格式（py 抽离批次 5）。

从 STATE_FILE env 读文件。输出错误行（每行一个），无错误输出空。
"""

import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("agate-state-yaml-check: 需要 pyyaml\n")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from agate_common import TASK_ID_RE
except Exception:  # 安装破损时回退内置（与 agate_common.TASK_ID_RE 同式）
    TASK_ID_RE = re.compile(r"^[A-Z]+[0-9]+$")

valid_phases = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "PAUSED", "READY", "DONE"]

state_file = os.environ["STATE_FILE"]
try:
    with open(state_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)
except yaml.YAMLError as e:
    print(f"YAML 解析错误: {e}")
    sys.exit(0)

errors = []

if data is None:
    errors.append("文件为空")
    print("\n".join(errors))
    sys.exit(0)

for field in ("task_id", "phase", "status"):
    if field not in data:
        errors.append(f"缺必填字段: {field}")

task_id = data.get("task_id", "")
if task_id and not TASK_ID_RE.match(str(task_id)):
    errors.append(f"task_id 格式错误: {task_id}（应为 ≥1 个大写字母 + 数字，如 TAG0001）")

phase = str(data.get("phase", ""))
if phase and phase not in valid_phases:
    errors.append("phase 非法值: {}（合法值: {}）".format(phase, " ".join(valid_phases)))

retries = data.get("retries", {})
if retries:
    if not isinstance(retries, dict):
        errors.append(f"retries 应为 dict，实际为 {type(retries).__name__}")
    else:
        for key, val in retries.items():
            if not re.match(r"^P\d+$", str(key)):
                errors.append(f"retries key 格式错误: {key}（应为大写 P + 数字，如 P2）")
            if not isinstance(val, list):
                errors.append(f"retries[{key}] 应为列表，实际为 {type(val).__name__}")

if errors:
    print("\n".join(errors))
