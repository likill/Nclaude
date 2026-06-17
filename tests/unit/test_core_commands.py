from __future__ import annotations

from pathlib import Path

from naohua_claude.cli.commands.core import _pid_file_for, _running_pid_for


# 功能：_pid_file_for 应根据项目状态目录返回正确的 pid 文件路径
# 设计：传入已知目录，验证返回路径包含 pid 文件名
def test_pid_file_for() -> None:
    pid_path = _pid_file_for(Path("/tmp/test-project-hash"))
    assert pid_path.name == "pid"
    assert "test-project-hash" in str(pid_path)


# 功能：pid 文件不存在时应返回 None
# 设计：用临时目录模拟不存在的 pid 文件
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
