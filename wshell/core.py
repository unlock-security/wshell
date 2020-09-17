import argparse
import sys
from typing import List, Union

from wshell.status import ExitStatus


# noinspection PyDefaultArgument
def main(args: List[Union[str, bytes]] = sys.argv) -> ExitStatus:
    """
    The main function.
    Process arguments and run the main workflow with error handling.
    Return exit status code.

    """
    pass


def program(args: argparse.Namespace) -> ExitStatus:
    """
    The main program without error handling.
    """
    pass
