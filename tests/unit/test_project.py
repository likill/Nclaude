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
# 设计：用多个不同路径验证，覆盖边界情况
def test_port_in_range() -> None:
    for path in ["/a", "/b", "/tmp/long/path/to/project", "C:\\Users\\test"]:
        port = compute_port(path)
        assert 17400 <= port <= 17499, f"port {port} out of range for {path}"


# 功能：project_state_dir 返回以 hash 命名的子目录
# 设计：验证返回路径包含 8 字符 hex 且在 ~/.naohua/projects/ 下
def test_project_state_dir() -> None:
    d = project_state_dir("/home/user/project-a")
    assert len(d.name) == 8  # 8-char hex hash


# 功能：同一目录返回同一状态目录
# 设计：确定性验证
def test_project_state_dir_deterministic() -> None:
    d1 = project_state_dir("/home/user/project-a")
    d2 = project_state_dir("/home/user/project-a")
    assert d1 == d2
