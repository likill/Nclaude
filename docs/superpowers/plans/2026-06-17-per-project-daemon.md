# Per-Project Daemon (方案3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow `naohua` to run independent daemons per project directory, so users can work in multiple folders simultaneously without port conflicts.

**Architecture:** The `naohua` CLI command computes a deterministic port from the current working directory (hash → port in range 17400-17499). It spawns a per-project daemon on that port, stores the PID in `~/.naohua/projects/<hash>/pid`, then launches the TUI. Each project directory gets its own isolated daemon+TUI pair. The `naohua-core` and `naohua-tui` commands remain unchanged for backward compatibility.

**Tech Stack:** Python, hashlib, pathlib, existing config/CLI/TUI infrastructure

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `src/naohua_claude/core/project.py` | **Create** | Port allocation from CWD hash, per-project state directory management |
| `tests/unit/test_project.py` | **Create** | Tests for port allocation and project state |
| `src/naohua_claude/cli/commands/core.py` | **Modify** | Per-project PID file path, pass computed port to daemon subprocess |
| `src/naohua_claude/cli/main.py` | **Modify** | `naohua` command: compute port from CWD, set env, start daemon, launch TUI |

---

### Task 1: Create project port allocation module

**Files:**
- Create: `src/naohua_claude/core/project.py`
- Create: `tests/unit/test_project.py`

- [ ] **Step 1: Write failing tests for port allocation**

```python
# tests/unit/test_project.py
from __future__ import annotations

from naohua_claude.core.project import compute_port, project_state_dir

# 功能：同一目录应始终算出相同的端口号（确定性）
# 设计：调用两次同一路径，断言结果相等，验证可重复性
def test_deterministic_port() -> None:
    port1 = compute_port("/home/user/project-a")
    port2 = compute_port("/home/user/project-a")
    assert port1 == port2

# 功能：不同目录应算出不同端口（大概率）
# 设计：用两个差异较大的路径，断言端口不同，排除碰撞
def test_different_dirs_different_ports() -> None:
    port_a = compute_port("/home/user/project-a")
    port_b = compute_port("/home/user/project-b")
    assert port_a != port_b

# 功能：端口必须在 17400-17499 范围内
# 设�：用多个不同路径验证，覆盖边界情况
def test_port_in_range() -> None:
    for path in ["/a", "/b", "/tmp/long/path/to/project", "C:\\Users\\test"]:
        port = compute_port(path)
        assert 17400 <= port <= 17499, f"port {port} out of range for {path}"

# 功能：project_state_dir 返回以 hash 命名的子目录
# 设�：验证返回路径包含 8 字符 hex 且在 ~/.naohua/projects/ 下
def test_project_state_dir() -> None:
    d = project_state_dir("/home/user/project-a")
    assert str(d).startswith(str(d.parent.parent))  # under ~/.naohua/projects/
    assert len(d.name) == 8  # 8-char hex hash

# 功能：同一目录返回同一状态目录
# 设计：确定性验证
def test_project_state_dir_deterministic() -> None:
    d1 = project_state_dir("/home/user/project-a")
    d2 = project_state_dir("/home/user/project-a")
    assert d1 == d2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_project.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'naohua_claude.core.project'"

- [ ] **Step 3: Implement project.py**

```python
# src/naohua_claude/core/project.py
from __future__ import annotations

import hashlib
from pathlib import Path

_PORT_BASE = 17400
_PORT_RANGE = 100  # 17400-17499
_PROJECTS_DIR = Path.home() / ".naohua" / "projects"


# 根据工作目录路径计算确定性端口号
def compute_port(cwd: str) -> int:
    h = hashlib.sha256(cwd.encode("utf-8")).hexdigest()
    offset = int(h[:8], 16) % _PORT_RANGE
    return _PORT_BASE + offset


# 返回当前项目的状态目录路径（含 pid 文件等）
def project_state_dir(cwd: str) -> Path:
    h = hashlib.sha256(cwd.encode("utf-8")).hexdigest()[:8]
    d = _PROJECTS_DIR / h
    d.mkdir(parents=True, exist_ok=True)
    return d
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_project.py -v`
Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/naohua_claude/core/project.py tests/unit/test_project.py
git commit -m "feat: add per-project port allocation module"
```

---

### Task 2: Modify CLI to support per-project daemon management

**Files:**
- Modify: `src/naohua_claude/cli/commands/core.py`
- Create: `tests/unit/test_core_commands.py`

- [ ] **Step 1: Write failing tests for per-project PID management**

```python
# tests/unit/test_core_commands.py
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from naohua_claude.cli.commands.core import _pid_file_for, _running_pid_for

# 功能：_pid_file_for 应根据项目状态目录返回正确的 pid 文件路径
# 设计：传入已知目录，验证返回路径包含 pid 文件名
def test_pid_file_for() -> None:
    pid_path = _pid_file_for(Path("/tmp/test-project-hash"))
    assert pid_path.name == "pid"
    assert "test-project-hash" in str(pid_path)

# 功能：pid 文件不存在时应返回 None
# 设-design：用临时目录模拟不存在的 pid 文件
def test_running_pid_no_file(tmp_path: Path) -> None:
    result = _running_pid_for(tmp_path / "nonexistent" / "pid")
    assert result is None

# 功能：pid 文件中的进程不存在时应返回 None 并清理文件
# 设计：写入一个不存在的 pid，验证返回 None 且文件被删除
def test_running_pid_stale_file(tmp_path: Path) -> None:
    pid_file = tmp_path / "pid"
    pid_file.write_text("999999999")  # 极大 pid，几乎不可能存在
    result = _running_pid_for(pid_file)
    assert result is None
    assert not pid_file.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_core_commands.py -v`
Expected: FAIL with import errors (functions don't exist yet)

- [ ] **Step 3: Modify cli/commands/core.py**

Replace the entire file with:

```python
from __future__ import annotations

import asyncio
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path

from naohua_claude.core.config import NaohuaConfig

# 兼容旧版单实例模式的全局 PID 文件（naohua-core 直接调用时使用）
_PID_FILE = Path.home() / ".naohua" / "naohua-core.pid"

logger = logging.getLogger(__name__)


# 返回指定项目状态目录下的 pid 文件路径
def _pid_file_for(state_dir: Path) -> Path:
    return state_dir / "pid"


# 读取 pid 文件并确认进程存活，已消失则删除文件返回 None
def _running_pid_for(pid_path: Path) -> int | None:
    if not pid_path.exists():
        return None
    try:
        pid = int(pid_path.read_text().strip())
        os.kill(pid, 0)
        return pid
    except (ValueError, ProcessLookupError, PermissionError):
        pid_path.unlink(missing_ok=True)
        return None


# 读取全局 PID 文件并确认进程存活（兼容旧模式）
def _running_pid() -> int | None:
    return _running_pid_for(_PID_FILE)


# 尝试连接 daemon，成功则正常返回，失败则抛出异常
async def _ping_check(config: NaohuaConfig) -> None:
    _r, w = await asyncio.open_connection(config.host, config.port)
    w.close()
    await w.wait_closed()


# 打印 daemon 当前状态（running / not running）
def cmd_core_status(config: NaohuaConfig) -> None:
    try:
        asyncio.run(_ping_check(config))
        print(f"running  ({config.host}:{config.port})")
    except (ConnectionRefusedError, OSError):
        print("not running")


# 在后台启动 daemon，若已在运行则提示并退出
def cmd_core_start(config: NaohuaConfig, state_dir: Path | None = None) -> None:
    pid_file = _pid_file_for(state_dir) if state_dir else _PID_FILE

    try:
        asyncio.run(_ping_check(config))
        print(f"already running  ({config.host}:{config.port})")
        return
    except (ConnectionRefusedError, OSError):
        pass

    env = os.environ.copy()
    env["NAOHUA_PORT"] = str(config.port)

    proc = subprocess.Popen(
        [sys.executable, "-m", "naohua_claude.core"],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(proc.pid))
    print(f"started  pid={proc.pid}  ({config.host}:{config.port})")


# 向 daemon 发送 SIGTERM 停止进程，若未运行则提示
def cmd_core_stop(config: NaohuaConfig, state_dir: Path | None = None) -> None:
    pid_file = _pid_file_for(state_dir) if state_dir else _PID_FILE
    pid = _running_pid_for(pid_file)
    if pid is None:
        print("not running")
        return
    os.kill(pid, signal.SIGTERM)
    pid_file.unlink(missing_ok=True)
    print(f"stopped  pid={pid}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_core_commands.py -v`
Expected: all 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/naohua_claude/cli/commands/core.py tests/unit/test_core_commands.py
git commit -m "feat: support per-project daemon PID management"
```

---

### Task 3: Modify `naohua` command to auto-manage per-project daemon

**Files:**
- Modify: `src/naohua_claude/cli/main.py`

- [ ] **Step 1: Modify cli/main.py to use per-project daemon**

Replace the `main()` function with the new version that computes port from CWD, starts per-project daemon, then launches TUI:

```python
from __future__ import annotations

import argparse
import os
import sys

from naohua_claude.cli.commands.chat import cmd_chat
from naohua_claude.cli.commands.core import cmd_core_start, cmd_core_status, cmd_core_stop
from naohua_claude.cli.commands.ping import cmd_ping
from naohua_claude.cli.commands.run import cmd_run
from naohua_claude.cli.commands.trace import cmd_trace
from naohua_claude.cli.commands.version import cmd_version
from naohua_claude.core.config import get_config
from naohua_claude.core.logging_setup import setup_logging


# CLI 主入口：解析命令行参数并分发到对应子命令
def main() -> None:
    parser = argparse.ArgumentParser(prog="naohua", description="NaohuaClaude CLI")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("ping", help="Ping the core daemon")
    subparsers.add_parser("chat", help="Start a multi-turn chat session")

    run_parser = subparsers.add_parser("run", help="Run an agent task")
    run_parser.add_argument("--goal", required=True, help="Goal for the agent to accomplish")

    core_parser = subparsers.add_parser("core", help="Manage the core daemon")
    core_sub = core_parser.add_subparsers(dest="core_command")
    core_sub.add_parser("start", help="Start the daemon in the background")
    core_sub.add_parser("stop", help="Stop the running daemon")
    core_sub.add_parser("status", help="Show daemon status")

    trace_parser = subparsers.add_parser("trace", help="View system trace log")
    trace_parser.add_argument("run_id", nargs="?", default=None, help="Filter by run ID")
    trace_parser.add_argument("--layer", choices=["ipc", "event", "llm"], help="Filter by layer")
    trace_parser.add_argument("--direction", help="Filter by direction (e.g. CORE→LLM)")
    trace_parser.add_argument("--raw", action="store_true", help="Output raw NDJSON")
    trace_parser.add_argument("--follow", "-f", action="store_true", help="Follow new records")

    args = parser.parse_args()

    if args.version:
        cmd_version()
        return

    # 无子命令时：per-project daemon + TUI
    if args.command is None:
        _start_project_daemon_and_tui()
        return

    config = get_config()
    setup_logging(config)

    if args.command == "ping":
        cmd_ping(config)
    elif args.command == "chat":
        cmd_chat(config)
    elif args.command == "run":
        cmd_run(args.goal, config)
    elif args.command == "core":
        if args.core_command == "start":
            cmd_core_start(config)
        elif args.core_command == "stop":
            cmd_core_stop(config)
        elif args.core_command == "status":
            cmd_core_status(config)
        else:
            core_parser.print_help()
            sys.exit(1)
    elif args.command == "trace":
        cmd_trace(
            args.run_id,
            config,
            layer=args.layer,
            direction=args.direction,
            raw=args.raw,
            follow=args.follow,
        )
    else:
        parser.print_help()
        sys.exit(1)


# 根据当前目录计算端口，启动专属 daemon，然后打开 TUI
def _start_project_daemon_and_tui() -> None:
    from naohua_claude.core.project import compute_port, project_state_dir

    cwd = os.getcwd()
    port = compute_port(cwd)
    state_dir = project_state_dir(cwd)

    os.environ["NAOHUA_PORT"] = str(port)

    config = get_config()
    setup_logging(config)

    cmd_core_start(config, state_dir=state_dir)

    from naohua_claude.tui.__main__ import main as tui_main
    tui_main()
```

- [ ] **Step 2: Manual test - verify `naohua` starts per-project daemon**

Run from project directory:
```cmd
cd D:\KamaClaude-main
C:\Users\Lenovo\.local\bin\naohua.exe
```
Expected: daemon starts on computed port, TUI opens and connects.

Run from a different directory:
```cmd
cd D:\naotest
C:\Users\Lenovo\.local\bin\naohua.exe
```
Expected: separate daemon starts on a different port, TUI opens and connects.

- [ ] **Step 3: Verify multiple daemons can coexist**

Open two terminals:
```cmd
# Terminal 1
cd D:\KamaClaude-main && C:\Users\Lenovo\.local\bin\naohua.exe

# Terminal 2
cd D:\naotest && C:\Users\Lenovo\.local\bin\naohua.exe
```
Expected: both daemons start on different ports, both TUIs work independently.

- [ ] **Step 4: Commit**

```bash
git add src/naohua_claude/cli/main.py
git commit -m "feat: naohua command auto-manages per-project daemon"
```

---

### Task 4: Verify backward compatibility

- [ ] **Step 1: Verify `naohua-core` still works standalone**

```cmd
naohua-core
```
Expected: starts on default port 7437 (unchanged behavior)

- [ ] **Step 2: Verify `naohua-tui` still works standalone**

```cmd
naohua-tui
```
Expected: connects to default port 7437 (unchanged behavior)

- [ ] **Step 3: Verify `naohua ping` still works**

```cmd
naohua ping
```
Expected: pings daemon on configured port

- [ ] **Step 4: Run full test suite**

```cmd
uv run pytest tests/ -v
```
Expected: all tests pass

- [ ] **Step 5: Run linter**

```cmd
uv run ruff check src tests
```
Expected: no errors

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat: per-project daemon support (方案3) complete"
```

---

## Design Notes

### Port allocation algorithm
- `hashlib.sha256(cwd.encode("utf-8")).hexdigest()[:8]` → `int(hex, 16) % 100` → `+ 17400`
- Range: 17400-17499 (100 ports, collision probability ~1% for 10 projects)
- Deterministic: same directory always gets same port

### Per-project state
- `~/.naohua/projects/<8-char-hex>/pid` — PID file for each project's daemon
- The 8-char hex is the prefix of the SHA256 hash of the absolute CWD path

### Backward compatibility
- `naohua-core` (direct) → still uses default port 7437, global PID file
- `naohua-tui` (direct) → still connects to whatever port is in config
- `naohua` (no subcommand) → NEW behavior: per-project daemon + TUI
- All subcommands (`ping`, `chat`, `run`, `core`, `trace`) → unchanged
