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
    except (ValueError, OSError):
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
