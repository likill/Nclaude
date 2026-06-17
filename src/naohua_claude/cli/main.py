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
    try:
        tui_main()
    finally:
        cmd_core_stop(config, state_dir=state_dir)
