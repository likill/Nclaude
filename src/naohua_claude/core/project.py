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
