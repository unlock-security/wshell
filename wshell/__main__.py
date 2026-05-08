#!/usr/bin/env python3
"""The main entry point. Invoke as `wshell` or `python3 -m wshell`."""

from __future__ import annotations

import sys

from wshell.arguments import parse_args
from wshell.config import Config
from wshell.errors import WShellError
from wshell.injectors import get_command_injector
from wshell.log import logger
from wshell.status import ExitStatus
from wshell.update import Updater


def main(argv: list[str] = sys.argv) -> ExitStatus:
    """Process arguments and run the main workflow."""
    try:
        parsed_args = parse_args(argv[1:])
        config = Config.from_args(parsed_args)
        logger.setLevel(config.log_level)

        if config.check_for_updates:
            Updater(config.include_prerelease).update()

        from wshell.cmd import WShellCmd

        WShellCmd(
            injector=get_command_injector(config),
            persistent_history_file=config.history_file,
        ).cmdloop()
    except WShellError as error:
        logger.error(f"{error.__class__.__name__}: {error}")
        return error.EXIT_STATUS

    return ExitStatus.SUCCESS


if __name__ == "__main__":
    try:
        exit_status = main()
    except KeyboardInterrupt:
        from .status import ExitStatus

        exit_status = ExitStatus.ERROR_CTRL_C

    sys.exit(exit_status)
