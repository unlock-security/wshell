#!/usr/bin/env python3
"""The main entry point. Invoke as `wshell' or `python3 -m wshell'."""

import sys


def main():
    try:
        from .core import main
        exit_status = main()
    except KeyboardInterrupt:
        from .status import ExitStatus
        exit_status = ExitStatus.ERROR_CTRL_C

    sys.exit(exit_status)


if __name__ == "__main__":
    main()
