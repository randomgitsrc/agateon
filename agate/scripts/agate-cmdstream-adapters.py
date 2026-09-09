#!/usr/bin/env python3
"""agate-cmdstream-adapters.py — 三平台命令流适配器（TAG0028，RM-AG0055）

从平台会话记录外部获取 subagent 活动信号（命令流日志），统一收敛为 CommandRecord IR
（见 agate-cmdstream-ir.py）。检测引擎只消费 IR、不感知平台细节——新增平台只需实现
CommandStreamAdapter 契约 + 注册表加一行（P2-design.md §3.1 M2 / BDD-2~7）。

适配器契约（基类）：
  probe(path) -> bool                       判断 path 是否为本平台会话文件
  list_sessions(cwd) -> list[str]           定位会话文件（含子 agent 会话）
  read_commands(session_path) -> list[CommandRecord]  解析命令流

平台差异（verification-cmdstream-datasource-20260903.md，R1）：
  - claude-code：JSONL，tool_use/tool_result 按 tool_use_id/sourceToolAssistantUUID ↔
    id/uuid 配对；无数字 exit code，靠 is_error + "Exit code N" 文本前缀解析
  - opencode：SQLite（opencode.db），part.data.state 嵌套对象；exit 取
    state.metadata.exit 整数、truncated 取 state.metadata.truncated 显式标记（R10：
    以验证记录 SQLite 为准，不用 storage/session/ 目录描述）
  - dsh：JSONL.zstd 拼接帧容器；解压隔离在本适配器内部（spawn node 单行脚本
    node:zlib.zstdDecompressSync，逐帧解压后拼接），不硬依赖 python zstandard；
    tool/call + tool/result 按 callId 配对；无数字 exit code，靠 isError + "Error:"
    文本前缀解析（BDD-4，dispatch-context 约束 5）

子 agent 会话定位（BDD-5）：
  - claude-code：会话目录 sidecar subagents/agent-*.jsonl 独立转录文件
  - dsh：delegationDepth>0 的独立 session 文件（.jsonl.zstd）
  - opencode：单库内按 message/session 归属区分（list_sessions 返回库内会话）

依赖：仅标准库（importlib 动态加载兄弟模块 agate-cmdstream-ir.py——连字符文件名
不能直接 import，参考 agate_common 被 import 的既有模式）。
"""

import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- 兄弟模块动态加载（连字符文件名不能直接 import） ----

_IR_CACHE = {}


def _load_ir():
    """importlib 加载 agate-cmdstream-ir.py，返回模块（带缓存，幂等）。"""
    if "ir" in _IR_CACHE:
        return _IR_CACHE["ir"]
    path = os.path.join(_SCRIPT_DIR, "agate-cmdstream-ir.py")
    spec = importlib.util.spec_from_file_location("agate_cmdstream_ir", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _IR_CACHE["ir"] = mod
    return mod


_IR = _load_ir()
CommandRecord = _IR.CommandRecord

# ---- 通用小工具 ----


def _sha1_hex(text):
    """输出内容哈希（截断输出不参与哈希比对，调用方负责 truncated 处理）。"""
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()


def _iso8601_to_epoch_ms(ts):
    """ISO-8601 UTC 时间戳（毫秒精度，如 2026-09-03T02:01:00.000Z）→ epoch 毫秒 int。

    非字符串输入（int/None 等畸形外部数据）抛 TypeError——落入调用方既有
    except (ValueError, TypeError) 分支，不让 AttributeError 传播崩溃 read_commands
    （CRITICAL-4 fix2 残留链 1）。
    """
    from datetime import datetime, timezone

    if not isinstance(ts, str):
        raise TypeError(f"timestamp 必须为字符串，收到 {type(ts).__name__}")
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


# ---- 适配器基类 ----


class CommandStreamAdapter:
    """命令流适配器基类：定义 probe/list_sessions/read_commands 契约（P2 §3.1 M2）。"""

    platform = "base"

    def probe(self, path):
        """判断 path 是否为本平台会话文件。"""
        raise NotImplementedError

    def list_sessions(self, cwd):
        """定位 cwd 下本平台会话文件（含子 agent 会话），返回绝对路径列表。"""
        raise NotImplementedError

    def read_commands(self, session_path):
        """解析会话文件 → CommandRecord 列表。"""
        raise NotImplementedError


# ---- Claude Code 适配器（JSONL + "Exit code N" 文本前缀） ----


class ClaudeCodeAdapter(CommandStreamAdapter):
    """Claude Code：~/.claude/projects/<dir>/<session>.jsonl。

    tool_use（assistant 行 content[] part）与 tool_result（user 行 content[] part）
    按 tool_result.tool_use_id / sourceToolAssistantUUID ↔ tool_use.id / uuid 配对；
    command 取 tool_use.input.command；ts 取各行 timestamp；exit 从 is_error +
    "Exit code N" 文本前缀解析，exit_signal 留档原始形态（BDD-2 / 验证记录 Q5）。
    子 agent = 会话目录 sidecar subagents/agent-*.jsonl（BDD-5）。
    """

    platform = "claude-code"

    def probe(self, path):
        return isinstance(path, str) and path.endswith(".jsonl") and not path.endswith(".zstd")

    def list_sessions(self, cwd):
        """递归定位 *.jsonl（含 subagents/ 下子转录文件，BDD-5）。"""
        sessions = []
        for root, _dirs, names in os.walk(cwd):
            for name in sorted(names):
                if name.endswith(".jsonl") and not name.endswith(".jsonl.zstd"):
                    sessions.append(os.path.join(root, name))
        return sessions

    def read_commands(self, session_path):
        session_id = os.path.basename(session_path)
        uses = []  # tool_use part 列表
        results = []  # tool_result part 列表
        skipped = 0  # 畸形/非法行计数（CRITICAL-4：不崩溃、计数告警）
        with open(session_path, encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    skipped += 1
                    continue
                if not isinstance(obj, dict):
                    skipped += 1
                    continue
                self._collect_parts(obj, uses, results)
        if skipped:
            sys.stderr.write(
                f"claude-code 适配器: {session_id} 跳过 {skipped} 行畸形/非法 JSON\n"
            )

        result_by_id = {}
        for r in results:
            rid = r.get("tool_use_id") or r.get("sourceToolAssistantUUID")
            if rid:
                result_by_id[rid] = r

        records = []
        dropped = 0  # timestamp 缺失/非法被跳过的配对计数（CRITICAL-4 防静默吞数据）
        for u in uses:
            uid = u.get("id") or u.get("uuid")
            if not uid:
                continue
            r = result_by_id.get(uid)
            rec = self._build_record(session_id, u, r)
            if rec is None:
                dropped += 1
                continue
            records.append(rec)
        if dropped:
            sys.stderr.write(
                f"claude-code 适配器: {session_id} 跳过 {dropped} 条 timestamp 缺失/非法的配对\n"
            )
        return records

    @staticmethod
    def _collect_parts(obj, uses, results):
        """从一行 JSON 对象收集 content[] 中的 tool_use / tool_result part。"""
        if not isinstance(obj, dict):  # CRITICAL-4：非 dict 行守卫
            return
        parts = []
        content = obj.get("content")
        if isinstance(content, list):
            parts.extend(p for p in content if isinstance(p, dict))
        if obj.get("type") == "tool_use":
            uses.append(obj)
        elif obj.get("type") == "tool_result":
            results.append(obj)
        for p in parts:
            if p.get("type") == "tool_use":
                uses.append(p)
            elif p.get("type") == "tool_result":
                results.append(p)

    @staticmethod
    def _build_record(session_id, u, r=None):
        """tool_use + 可选 tool_result 配对 → CommandRecord。

        exit 解析（验证记录 Q5 / BDD-2）：无数字 exit 字段；is_error 布尔 + 输出文本
        前缀 "Exit code N" → 数字 exit；exit_signal 留档原始形态。
        未结束 call（r is None）→ exit=None / ts_end=None / exit_signal="pending"
        （CRITICAL-3：IR 契约允许 exit=None；ts_end 放宽为 int|None 表达未结束）。
        timestamp 缺失/非法 → 返回 None（该配对跳过，不产出坏记录，CRITICAL-4）。
        """
        try:
            ts_start = _iso8601_to_epoch_ms(u.get("timestamp", ""))
        except (ValueError, TypeError):
            return None

        input_cmd = u.get("input", {})
        command = input_cmd.get("command", "") if isinstance(input_cmd, dict) else ""
        tool = u.get("name", "")

        if r is None:
            return CommandRecord(
                platform="claude-code",
                session_id=session_id,
                tool=tool,
                command=command,
                ts_start=ts_start,
                ts_end=None,
                exit=None,
                exit_signal="pending",
                output_hash=None,
                truncated=False,
            )

        try:
            ts_end = _iso8601_to_epoch_ms(r.get("timestamp", ""))
        except (ValueError, TypeError):
            ts_end = None  # 结束时间缺失：保留记录、结束时间未知（不崩溃）

        content = r.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    text_parts.append(str(item.get("text", "")))
                else:
                    text_parts.append(str(item))
            content = "\n".join(text_parts)
        content = str(content or "")

        is_error = bool(r.get("is_error", False))
        exit_code = None
        exit_signal = ""
        m = re.search(r"Exit code (\d+)", content)
        if m:
            exit_code = int(m.group(1))
            exit_signal = m.group(0)
        elif is_error:
            exit_signal = "is_error=true"
        else:
            exit_code = 0

        # CRITICAL-4 fix2 残留链 2：toolUseResult 为非空非 dict（如字符串）时
        # `(r.get("toolUseResult") or {}).get("isImage")` 会 AttributeError——
        # 先取引用再 isinstance 守卫，非 dict 不触发 .get。
        tr = r.get("toolUseResult")
        truncated = bool(r.get("truncated", False)) or (
            isinstance(tr, dict) and bool(tr.get("isImage", False))
        )
        output_hash = None if truncated else _sha1_hex(content)
        return CommandRecord(
            platform="claude-code",
            session_id=session_id,
            tool=tool,
            command=command,
            ts_start=ts_start,
            ts_end=ts_end,
            exit=exit_code,
            exit_signal=exit_signal,
            output_hash=output_hash,
            truncated=truncated,
        )


# ---- OpenCode 适配器（SQLite + metadata.exit 整数） ----


class OpenCodeAdapter(CommandStreamAdapter):
    """OpenCode：~/.local/share/opencode/opencode.db（单一 SQLite 库，R10 以验证记录为准）。

    part.data.state 嵌套对象：command=state.input.command、ts=state.time.start/end、
    exit=state.metadata.exit（整数，干净字段）、truncated=state.metadata.truncated
    （显式标记）（BDD-3）。子 agent 会话按 message/session 归属区分（list_sessions
    返回库内不同 session id）。
    """

    platform = "opencode"

    def probe(self, path):
        return isinstance(path, str) and (
            os.path.basename(path) == "opencode.db" or path.endswith(".db")
        )

    def list_sessions(self, cwd):
        """定位 cwd 下 opencode.db 库文件；返回库内 session id 定位串。"""
        found = []
        for root, _dirs, names in os.walk(cwd):
            for name in names:
                if name == "opencode.db":
                    found.append(os.path.join(root, name))
        return found

    def read_commands(self, session_path):
        session_id = os.path.basename(session_path)
        records = []
        if not os.path.isfile(session_path):
            return records
        # CRITICAL-5：DB 文件在用户目录（外部不可信输入）——非 SQLite 文件/缺表/损坏库
        # 一律返回空列表 + stderr 告警，不让 DatabaseError 传播崩溃 read_commands。
        try:
            conn = sqlite3.connect(session_path)
        except sqlite3.Error as e:
            sys.stderr.write(f"opencode 适配器: 无法打开 SQLite 库 {session_path}: {e}\n")
            return records
        try:
            cur = conn.execute("SELECT data FROM part")
            for (data_blob,) in cur:
                if not data_blob:
                    continue
                try:
                    data = json.loads(data_blob)
                except (ValueError, TypeError):
                    continue
                rec = self._state_to_record(session_id, data)
                if rec is not None:
                    records.append(rec)
        except sqlite3.Error as e:
            sys.stderr.write(
                f"opencode 适配器: 读取 part 表失败（非 SQLite/缺表/损坏库）{session_path}: {e}\n"
            )
            records = []
        finally:
            conn.close()
        return records

    @staticmethod
    def _state_to_record(session_id, data):
        """part.data → CommandRecord（state 嵌套对象，BDD-3）。

        fixture 为双重嵌套（part.data.state.state，P3 fixture 结构），实机为单层
        （part.data.state 直接含 input/metadata/time，验证记录样例）——逐层解包到
        含 input 键的最内层 state。
        """
        if not isinstance(data, dict):
            return None
        state = data.get("state")
        while isinstance(state, dict) and "input" not in state and isinstance(state.get("state"), dict):
            state = state["state"]
        if not isinstance(state, dict):
            return None
        input_obj = state.get("input", {})
        command = input_obj.get("command", "") if isinstance(input_obj, dict) else ""
        tool = state.get("tool") or data.get("tool") or ""
        time_obj = state.get("time", {}) if isinstance(state.get("time"), dict) else {}
        ts_start = time_obj.get("start")
        ts_end = time_obj.get("end")
        metadata = state.get("metadata", {}) if isinstance(state.get("metadata"), dict) else {}
        exit_code = metadata.get("exit")
        truncated = bool(metadata.get("truncated", False))
        output = state.get("output", "")
        output_hash = None if truncated else _sha1_hex(str(output or ""))
        return CommandRecord(
            platform="opencode",
            session_id=session_id,
            tool=str(tool),
            command=str(command),
            ts_start=int(ts_start) if isinstance(ts_start, int) else None,
            ts_end=int(ts_end) if isinstance(ts_end, int) else None,
            exit=exit_code if isinstance(exit_code, int) else None,
            exit_signal="metadata.exit" if isinstance(exit_code, int) else "",
            output_hash=output_hash,
            truncated=truncated,
        )


# ---- DSH 适配器（JSONL.zstd 拼接帧 + node zstd 解压隔离） ----


class DSHAdapter(CommandStreamAdapter):
    """DSH：~/.dsh/sessions/<sanitized-cwd>/<session-id>/session.jsonl.zstd。

    拼接帧容器逐帧解压（spawn node 单行脚本 node:zlib.zstdDecompressSync，解压全程
    隔离在本适配器内部——BDD-4 / dispatch-context 约束 5，不依赖 python zstandard）；
    tool/call + tool/result 按 callId 配对产出 ts_start/ts_end；command 取
    data.arguments.command（JSON 字符串）；exit 从 isError + "Error:" 文本前缀解析并写
    exit_signal；子 agent = delegationDepth>0 独立 session 文件（BDD-5）。
    """

    platform = "dsh"

    def probe(self, path):
        return isinstance(path, str) and path.endswith(".jsonl.zstd")

    def list_sessions(self, cwd):
        """递归定位 *.jsonl.zstd（含 delegationDepth>0 子 session，BDD-5）。"""
        sessions = []
        for root, _dirs, names in os.walk(cwd):
            for name in sorted(names):
                if name.endswith(".jsonl.zstd"):
                    sessions.append(os.path.join(root, name))
        return sessions

    def _node_zstd_available(self):
        node = shutil.which("node")
        if not node:
            return False, "node 不可用"
        try:
            proc = subprocess.run(
                [node, "-e",
                 "const z=require('node:zlib');"
                 "process.stdout.write(typeof z.zstdDecompressSync)"],
                capture_output=True, text=True, encoding="utf-8", timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False, "node zstd 探测失败"
        return proc.returncode == 0 and "function" in proc.stdout, ""

    def _decompress(self, session_path):
        """node 单行脚本逐帧解压拼接帧容器 → 明文 JSONL 文本（BDD-4 解压隔离）。

        CRITICAL-2：zstd 拼接帧容器（验证记录 Q7：实测 20020 帧）不能一次解压——Node
        zstdDecompressSync 对多帧输入只解第一帧。脚本按 zstd 帧 magic 0x28B52FFD 扫描
        帧边界、逐帧解压后拼接（验证记录「需扫描帧边界逐个解压后拼接」结论落地）。
        """
        ok, err = self._node_zstd_available()
        if not ok:
            raise RuntimeError(f"DSH 适配器需要 node:zlib.zstdDecompressSync 解压会话文件（{err}）")
        node = shutil.which("node")
        script = (
            "const z=require('node:zlib');const fs=require('fs');"
            "const buf=fs.readFileSync(process.argv[1]);"
            "const MAGIC=Buffer.from([0x28,0xb5,0x2f,0xfd]);"
            "let chunks=[];let off=0;"
            "while(off<buf.length){"
            "const idx=buf.indexOf(MAGIC,off);"
            "if(idx<0)break;"
            "try{"
            "const dec=z.zstdDecompressSync(buf.subarray(idx));"
            "chunks.push(dec);"
            "off=idx+4;"  # 推进到 magic 之后，下一轮 indexOf 定位下一帧
            "}catch(e){off=idx+1;}"  # 数据内伪 magic：跳过 1 字节继续扫
            "}"
            "process.stdout.write(Buffer.concat(chunks));"
        )
        proc = subprocess.run(
            [node, "-e", script, session_path],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"DSH zstd 解压失败: {proc.stderr[:200]}")
        return proc.stdout

    @staticmethod
    def _detect_truncated(first):
        """DSH result content 截断标记检测（CRITICAL-7）。

        验证记录 Q6 仅确认 DSH「有截断标记（超大输出会被截断）」未给字段名；采用双信号：
        ① tool-result dict 上的显式布尔字段（truncated / isTruncated）；
        ② 输出文本中的截断标记字面量（"[truncated]" / "…[truncated]" / "Output truncated"，
        不区分大小写）。任一命中即视为截断。
        """
        if not isinstance(first, dict):
            return False
        for key in ("truncated", "isTruncated"):
            val = first.get(key)
            if isinstance(val, bool) and val:
                return True
        inner = first.get("content")
        if isinstance(inner, list):
            text = "".join(
                str(item.get("text", "")) for item in inner if isinstance(item, dict)
            )
        elif isinstance(inner, str):
            text = inner
        else:
            text = ""
        lowered = text.lower()
        return any(
            marker in lowered
            for marker in ("[truncated]", "…[truncated]", "output truncated")
        )

    def read_commands(self, session_path):
        session_id = os.path.basename(session_path)
        text = self._decompress(session_path)
        calls = {}  # callId → 事件
        results = []  # result 事件列表（保序）
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if not isinstance(obj, dict):  # CRITICAL-4：畸形行守卫
                continue
            etype = obj.get("type")
            if etype == "tool/call":
                data = obj.get("data")
                if not isinstance(data, dict):
                    continue
                call_id = data.get("callId") or ""
                if call_id:
                    calls[call_id] = obj
            elif etype == "tool/result":
                results.append(obj)

        records = []
        matched = set()  # 已配对 result 的 callId（CRITICAL-3）
        for res in results:
            data = res.get("data", {}) if isinstance(res.get("data"), dict) else {}
            message = data.get("message", {}) if isinstance(data.get("message"), dict) else {}
            source = message.get("source", {}) if isinstance(message.get("source"), dict) else {}
            content_list = message.get("content")
            call_id = ""
            is_error = False
            text_out = ""
            truncated = False
            if isinstance(content_list, list) and content_list:
                first = content_list[0]
                if isinstance(first, dict):
                    call_id = first.get("toolCallId") or source.get("callId") or ""
                    is_error = bool(first.get("isError", False))
                    truncated = self._detect_truncated(first)
                    inner = first.get("content")
                    if isinstance(inner, list):
                        text_out = "".join(
                            str(item.get("text", "")) for item in inner
                            if isinstance(item, dict)
                        )
                    elif isinstance(inner, str):
                        text_out = inner
            call = calls.get(call_id)
            if call is None:
                continue
            matched.add(call_id)
            records.append(
                self._build_record(session_id, call, res, call_id, is_error, text_out, truncated)
            )
        # CRITICAL-3：未结束 call（call 无配对 result）→ 产出 exit=None/ts_end=None 记录
        for call_id, call in calls.items():
            if call_id in matched:
                continue
            records.append(self._build_record(session_id, call, None, call_id, False, "", False))
        # 监控视角：最新事件在前（拼接帧容器边写边落，倒序返回让"最近活动"优先可见）。
        # 注意：检测引擎按事件 ts 计算（不依赖列表顺序），本顺序不影响 detect 语义。
        return records[::-1]

    @staticmethod
    def _build_record(session_id, call, res, call_id, is_error, text_out, truncated=False):
        call_data = call.get("data", {}) if isinstance(call.get("data"), dict) else {}
        name = call_data.get("name", "")
        args = call_data.get("arguments", "")
        command = ""
        if isinstance(args, str):
            try:
                parsed = json.loads(args)
                if isinstance(parsed, dict):
                    command = parsed.get("command", "")
            except ValueError:
                command = args
        elif isinstance(args, dict):
            command = args.get("command", "")
        ts_start = call.get("time")
        ts_end = res.get("time") if res is not None else None

        if res is None:
            # CRITICAL-3：未结束 call（无配对 result）→ exit=None / ts_end=None / "pending"
            return CommandRecord(
                platform="dsh",
                session_id=session_id,
                tool=str(name),
                command=str(command),
                ts_start=int(ts_start) if isinstance(ts_start, int) else None,
                ts_end=None,
                exit=None,
                exit_signal="pending",
                output_hash=None,
                truncated=False,
            )

        exit_code = None
        if is_error:
            exit_signal = "Error:" if re.search(r"Error:", text_out) else "isError=true"
        else:
            exit_code = 0
            exit_signal = ""

        # CRITICAL-7：截断标记命中 → truncated=True 且 output_hash=None（IR 契约）
        output_hash = None if truncated else _sha1_hex(text_out)
        return CommandRecord(
            platform="dsh",
            session_id=session_id,
            tool=str(name),
            command=str(command),
            ts_start=int(ts_start) if isinstance(ts_start, int) else None,
            ts_end=int(ts_end) if isinstance(ts_end, int) else None,
            exit=exit_code,
            exit_signal=exit_signal,
            output_hash=output_hash,
            truncated=truncated,
        )


# ---- Codex 适配器（rollout JSONL + item.exit_code 数字 exit code） ----

# P5 V4 收敛锚：Codex 截断标记形态实测后收敛此常量/方法（P1 §4.1.2 / §7 V4）
_CODEX_TRUNC_BOOL_KEYS = ("truncated", "output_truncated", "is_truncated")
_CODEX_TRUNC_TEXT_MARKERS = (
    "[output truncated]",
    "output truncated",
    "tokens truncated",
    "[truncated]",
)


def _codex_int_or_none(val):
    """epoch 毫秒字段取整数（bool 不算 int，畸形外部数据 → None）。"""
    if isinstance(val, bool):
        return None
    return val if isinstance(val, int) else None


def _codex_is_finished(payload, item):
    """Codex CommandExecution item 是否已结束——「无终态信号才算 pending」口径。

    P6 V6 实测修正（DEBT0035）：真机 Codex 把**已结束但非 0 退出**的命令记为
    ``item.status == "failed"``（不是 ``"completed"``），且该 item 仍携带完整
    ``exit_code`` + ``payload.completed_at_ms``。旧口径 ``status != "completed"`` 把这些
    已结束命令误判为 pending，丢失真实 exit_code + output_hash（→ detect 判不出 SPIN）。

    已结束的判据 = 三者任一成立：
    - ``item.status`` ∈ ``{"completed", "failed"}``（Codex 已知终态取值）
    - ``payload.completed_at_ms`` 非 None（有完成时刻）
    - ``item.exit_code`` 是 int 且非 bool（有退出码）

    仅 ``status`` ∈ ``{"in_progress", 其它未知}`` 且缺 completed_at_ms/exit_code 时才算
    未结束（真·pending）。
    """
    if isinstance(item, dict):
        if item.get("status") in ("completed", "failed"):
            return True
        raw_exit = item.get("exit_code")
        if isinstance(raw_exit, int) and not isinstance(raw_exit, bool):
            return True
    return isinstance(payload, dict) and payload.get("completed_at_ms") is not None


class CodexAdapter(CommandStreamAdapter):
    """Codex：~/.codex/sessions/YYYY/MM/DD/rollout-<ISO8601>-<uuid>.jsonl（rollout JSONL）。

    首行恒为 type=="session_meta"（payload 含 cli_version / originator / id）——probe 的正向
    信号（Claude Code 转录首行不具备）。命令流来自 type=="event_msg" 且
    payload.type=="item_completed" 且 payload.item.type=="CommandExecution" 的事件；
    exit 直接取 item.exit_code（数字，无需文本前缀解析），ts 取 payload.started_at_ms /
    completed_at_ms（epoch ms int）。未结束命令 = 有 item_started 无 item_completed（或
    item_completed 但无终态信号——status∉{completed,failed} 且缺 completed_at_ms/exit_code，
    _codex_is_finished）→ 回填 exit=None / ts_end=None / "pending" 记录（比照 DSHAdapter
    未结束 call 补记录）。真机 status=="failed" 携 exit_code 属已结束，走非 pending 路径
    （DEBT0035 / P6 V6）。截断走双信号兜底（_detect_truncated）。
    session_id = os.path.basename(session_path)（不取 payload.session_id——那对子会话是父 id）。
    父会话与 spawn_agent 子会话都是同目录独立 rollout-*.jsonl → os.walk 天然同时枚举。
    """

    platform = "codex"

    def probe(self, path):
        """basename rollout-*.jsonl（排除 .jsonl.zstd）+ 首行 session_meta 含 codex 标记。

        路径不存在 / 首行非 JSON / 非 dict / 无 codex 标记 → return False，绝不抛
        （比照 DSHAdapter.probe / ClaudeCodeAdapter.probe 的异常处理）。
        """
        try:
            if not isinstance(path, str):
                return False
            base = os.path.basename(path)
            if not base.startswith("rollout-"):
                return False
            if not base.endswith(".jsonl") or base.endswith(".jsonl.zstd"):
                return False
            with open(path, encoding="utf-8", errors="replace") as f:
                first = f.readline()
            obj = json.loads(first)
            if not isinstance(obj, dict) or obj.get("type") != "session_meta":
                return False
            payload = obj.get("payload")
            if not isinstance(payload, dict):
                return False
            return any(k in payload for k in ("cli_version", "originator", "id"))
        except (OSError, ValueError, TypeError):
            return False

    def list_sessions(self, cwd):
        """os.walk 枚举 rollout-*.jsonl（排除 .jsonl.zstd）；root = cwd if cwd else
        expanduser("~/.codex/sessions")（cwd 为 None / "" 都回落默认根——P2-review N1）。
        返回按路径字符串 sorted() 的绝对路径 list（文件名内嵌 ISO8601，字典序≈时间序）。"""
        root = cwd if cwd else os.path.expanduser("~/.codex/sessions")
        sessions = []
        for dirpath, _dirs, names in os.walk(root):
            for name in sorted(names):
                if (
                    name.startswith("rollout-")
                    and name.endswith(".jsonl")
                    and not name.endswith(".jsonl.zstd")
                ):
                    sessions.append(os.path.join(dirpath, name))
        return sorted(sessions)

    def read_commands(self, session_path):
        session_id = os.path.basename(session_path)
        records = []
        started = {}  # item.id → (obj, payload, item) 起始事件（item_started/item_updated）
        emitted_ids = set()  # 已产出记录的 item.id（去重 pending 回填）
        skipped = 0  # 畸形/非法行计数（不崩溃、计数告警，照 ClaudeCodeAdapter）
        try:
            fh = open(session_path, encoding="utf-8", errors="replace")
        except OSError:
            return records
        with fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    skipped += 1
                    continue
                if not isinstance(obj, dict):
                    skipped += 1
                    continue
                if obj.get("type") != "event_msg":
                    continue
                payload = obj.get("payload")
                if not isinstance(payload, dict):
                    skipped += 1
                    continue
                item = payload.get("item")
                if not isinstance(item, dict) or item.get("type") != "CommandExecution":
                    continue
                ptype = payload.get("type")
                item_id = item.get("id")
                if ptype in ("item_started", "item_updated"):
                    if item_id is not None and item_id not in started:
                        started[item_id] = (obj, payload, item)
                    continue
                if ptype != "item_completed":
                    continue
                pending = not _codex_is_finished(payload, item)
                records.append(
                    self._build_record(session_id, obj, payload, item, pending=pending)
                )
                if item_id is not None:
                    emitted_ids.add(item_id)
        # 未结束命令（P2 §5 设计点 2 / R3）：有 item_started 无对应 item_completed →
        # 补一条 pending 记录（比照 DSHAdapter line 556-560）。已完成命令记录不受影响。
        for item_id, (s_obj, s_payload, s_item) in started.items():
            if item_id in emitted_ids:
                continue
            records.append(
                self._build_record(session_id, s_obj, s_payload, s_item, pending=True)
            )
        if skipped:
            sys.stderr.write(
                f"codex 适配器: {session_id} 跳过 {skipped} 行畸形/非法 JSON\n"
            )
        return records

    @staticmethod
    def _join_command(command):
        """item.command 数组 → shlex.join（元素逐个 str 强转）；非 list → ""。"""
        if not isinstance(command, list):
            return ""
        return shlex.join(str(part) for part in command)

    @classmethod
    def _detect_truncated(cls, item):
        """Codex 输出截断双信号检测（P2 §5 设计点 4，比照 DSHAdapter._detect_truncated）。

        P5 V4 收敛锚：Codex 截断标记形态实测后收敛此常量/方法（P1 §4.1.2 / §7 V4）。
        ① item 上的显式布尔字段（_CODEX_TRUNC_BOOL_KEYS）；② aggregated_output /
        formatted_output 里的字面量标记（_CODEX_TRUNC_TEXT_MARKERS，小写子串）。
        任一命中 → True。
        """
        if not isinstance(item, dict):
            return False
        for key in _CODEX_TRUNC_BOOL_KEYS:
            val = item.get(key)
            if isinstance(val, bool) and val:
                return True
        text = ""
        for field in ("aggregated_output", "formatted_output"):
            v = item.get(field)
            if isinstance(v, str):
                text += v
        lowered = text.lower()
        return any(marker in lowered for marker in _CODEX_TRUNC_TEXT_MARKERS)

    def _build_record(self, session_id, obj, payload, item, *, pending):
        """event_msg/item_* 事件 → CommandRecord（十字段映射见 P2 §4.2）。

        pending（未结束）→ exit=None / ts_end=None / exit_signal="pending" /
        output_hash=None / truncated=False。已完成 → exit 直取 item.exit_code（数字，
        非 bool），exit_signal 留档原始形态。
        """
        command = self._join_command(item.get("command"))
        ts_start = _codex_int_or_none(payload.get("started_at_ms"))
        if ts_start is None:
            try:
                ts_start = _iso8601_to_epoch_ms(obj.get("timestamp", ""))
            except (ValueError, TypeError):
                ts_start = None

        if pending:
            return CommandRecord(
                platform="codex",
                session_id=session_id,
                tool="exec",
                command=command,
                ts_start=ts_start,
                ts_end=None,
                exit=None,
                exit_signal="pending",
                output_hash=None,
                truncated=False,
            )

        ts_end = _codex_int_or_none(payload.get("completed_at_ms"))
        raw_exit = item.get("exit_code")
        exit_code = (
            raw_exit if isinstance(raw_exit, int) and not isinstance(raw_exit, bool) else None
        )
        if exit_code is not None:
            exit_signal = f"exit_code={exit_code}"
        else:
            status = item.get("status")
            exit_signal = str(status) if status else "status=completed"
        truncated = self._detect_truncated(item)
        output = item.get("aggregated_output", "")
        output_hash = None if truncated else _sha1_hex(str(output or ""))
        return CommandRecord(
            platform="codex",
            session_id=session_id,
            tool="exec",
            command=command,
            ts_start=ts_start,
            ts_end=ts_end,
            exit=exit_code,
            exit_signal=exit_signal,
            output_hash=output_hash,
            truncated=truncated,
        )


# ---- 显式注册表（P2 §2.1 候选 A，BDD-6：配置声明形态） ----

ADAPTERS = {
    "claude-code": ClaudeCodeAdapter(),
    "opencode": OpenCodeAdapter(),
    "dsh": DSHAdapter(),
    "codex": CodexAdapter(),
}


if __name__ == "__main__":
    import sys

    sys.stderr.write(
        "agate-cmdstream-adapters.py 是被 import 的适配器模块（ADAPTERS 注册表），不直接执行\n"
    )
    sys.exit(1)
