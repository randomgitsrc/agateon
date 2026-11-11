#!/usr/bin/env python3
"""agate-cmdstream-ir.py — 命令流日志统一中间表示（CommandRecord IR）（TAG0028，RM-AG0055）

三平台命令流适配器（Claude Code JSONL / OpenCode SQLite / DSH JSONL.zstd）的解析结果
统一收敛为 CommandRecord（十字段），检测引擎只消费该 IR、不感知平台细节。

字段契约（BDD-1，P2-design.md §3.1 M1）：
  platform    平台标识（claude-code / opencode / dsh / 新增平台）
  session_id  会话标识（适配器从会话文件名/记录中解析）
  tool        工具名（如 Bash / bash）
  command     完整命令文本
  ts_start    命令开始 epoch 毫秒 int
  ts_end      命令结束 epoch 毫秒 int|None（None = 未结束 call / 结束时间未知，
              CRITICAL-3 修复：未结束 call 记录以 ts_end=None 显式表达）
  exit        退出码 int|None（None = 未结束 call / 无法解析；claude-code 与 dsh 无数字
              exit 字段，靠文本前缀解析失败时为 None）
  exit_signal 退出信号的原始形态留档（"Exit code N" / "Error:" 文本前缀、is_error 布尔、
              "pending" 等），供审计追溯解析规则（验证记录差异点 2）
  output_hash 输出内容哈希（truncated=True 时必为 None，截断输出不参与哈希比对）。
              ⚠️ 仅 adapter 侧做**装饰信息归一化**后再哈希（剥「整行就是时间」的装饰行与 pid），
              因为唯一消费方是空转判据（按 `(命令, exit, output_hash)` 判重复）；
              它**不是**原文字节的哈希，不可用于内容完整性校验。
  truncated   输出是否被截断（bool）

依赖：仅标准库（dataclasses / json）。
"""

import json
from dataclasses import asdict, dataclass

__all__ = ["CommandRecord", "from_json"]


@dataclass
class CommandRecord:
    """命令流日志统一中间表示（十字段字段契约，BDD-1）。"""

    platform: str
    session_id: str
    tool: str
    command: str
    ts_start: int
    ts_end: int | None = None
    exit: int | None = None
    exit_signal: str = ""
    output_hash: str | None = None
    truncated: bool = False

    def to_json(self):
        """序列化为 JSON 字符串（供 CLI 中间传递与测试断言）。"""
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=False)

    @classmethod
    def from_dict(cls, data):
        """从 dict 构造（校验十字段字段完整性 + 类型契约，BDD-1 Then / CRITICAL-6）。

        类型契约（P2-design §3.1 M1 + P4-review CRITICAL-6）：
          ts_start 须为 epoch 毫秒 int；ts_end int|None（None = 未结束 call）；
          exit int|None；truncated bool；output_hash str|None（truncated 时 None 由
          调用方保证，此处仅校验类型）；platform/session_id/tool/command/exit_signal str。
        不符抛 ValueError 带字段名——坏数据不得静默流入检测引擎。
        """
        required = (
            "platform", "session_id", "tool", "command",
            "ts_start", "ts_end", "exit", "exit_signal", "output_hash", "truncated",
        )
        missing = [f for f in required if f not in data]
        if missing:
            raise ValueError(f"CommandRecord 缺字段: {missing}")

        def _is_int(v):
            return isinstance(v, int) and not isinstance(v, bool)

        type_errors = []
        for f in ("platform", "session_id", "tool", "command", "exit_signal"):
            if not isinstance(data[f], str):
                type_errors.append(f"{f} 期望 str，实际 {type(data[f]).__name__}")
        if not _is_int(data["ts_start"]):
            type_errors.append(f"ts_start 期望 epoch 毫秒 int，实际 {type(data['ts_start']).__name__}")
        if data["ts_end"] is not None and not _is_int(data["ts_end"]):
            type_errors.append(f"ts_end 期望 int|None，实际 {type(data['ts_end']).__name__}")
        if data["exit"] is not None and not _is_int(data["exit"]):
            type_errors.append(f"exit 期望 int|None，实际 {type(data['exit']).__name__}")
        if not isinstance(data["truncated"], bool):
            type_errors.append(f"truncated 期望 bool，实际 {type(data['truncated']).__name__}")
        if data["output_hash"] is not None and not isinstance(data["output_hash"], str):
            type_errors.append(
                f"output_hash 期望 str|None，实际 {type(data['output_hash']).__name__}"
            )
        if type_errors:
            raise ValueError(f"CommandRecord 字段类型契约违规: {'; '.join(type_errors)}")
        return cls(**data)


def from_json(s):
    """模块级 from_json：JSON 字符串 → CommandRecord（BDD-1 序列化往返）。"""
    return CommandRecord.from_dict(json.loads(s))


if __name__ == "__main__":
    import sys

    sys.stderr.write("agate-cmdstream-ir.py 是被 import 的 IR 模块，不直接执行\n")
    sys.exit(1)
