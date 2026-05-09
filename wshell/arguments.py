"""
Argument parsing for WShell.
"""
from __future__ import annotations

import argparse
import os
import sys
import textwrap

import wshell.constants
from wshell import validators
from wshell.config import Config
from wshell.enums import OSEnum
from wshell.scripts import input_scripts, output_scripts


def parse_args(args: list[str]) -> argparse.Namespace:
    """
    Parses command-line arguments.
    """
    parser = argparse.ArgumentParser(
        prog="wshell",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Turn a web-based {code,command,template} injection in a full featured shell with ease",
        epilog=textwrap.dedent(f'''
            For every --ARGUMENT there is also a --no-ARGUMENT that reverts ARGUMENT

            Example usage:

                wshell 'https://www.example.com/webshell?cmd={Config.command_placeholder}'
                wshell --form 'https://www.example.com/command-injection' 'p=;{Config.command_placeholder} #'
                wshell 'https://www.example.com/ssti' 'msg=${{self.module.cache.util.os.system("{Config.command_placeholder}")}}'
        '''),
        add_help=True,
        allow_abbrev=False
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s v{wshell.constants.VERSION}",
        help="Show the version number and exit"
    )

    # WShell specific parameters
    parser.add_argument(
        "--placeholder",
        dest="command_placeholder",
        type=validators.not_empty,
        default=Config.command_placeholder,
        help="Use a custom command placeholder (default: %(default)s)"
    )
    parser.add_argument(
        "--prompt",
        type=validators.not_empty,
        help="Use a custom command prompt on REPL shell (default: mimic remote system prompt)"
    )
    parser.add_argument(
        "--os",
        default=None,
        choices=[*OSEnum],
        type=OSEnum,
        help="Specify OS and shell in use on the target (default: auto-discover)"
    )

    # HTTP-related parameters
    http_group = parser.add_argument_group(title='HTTP arguments')
    http_group.add_argument(
        "-m", "--method",
        help="The HTTP method to be used for the requests (Default: POST if there is some data, GET otherwise)"
    )
    timeout_http_group = http_group.add_mutually_exclusive_group(required=False)
    timeout_http_group.add_argument(
        "-t", "--timeout",
        metavar="SECONDS",
        type=validators.positive_float,
        default=Config.timeout,
        help="The connection timeout of the request in seconds (default: %(default)s)"
    )
    timeout_http_group.add_argument(
        "--no-timeout",
        action="store_const",
        dest="timeout",
        const=None,
        help=argparse.SUPPRESS
    )
    http_group.add_argument(
        "-d", "--delay",
        type=validators.positive_float,
        default=Config.delay,
        help="Delay in seconds between each HTTP request (default: %(default)s)"
    )
    persistent_connection_http_group = http_group.add_mutually_exclusive_group(required=False)
    persistent_connection_http_group.add_argument(
        "--keep-alive",
        action="store_true",
        dest="reuse_connection",
        default=Config.reuse_connection,
        help="Use persistent connection (default: %(default)s)"
    )
    persistent_connection_http_group.add_argument(
        "--no-keep-alive",
        action="store_false",
        dest="reuse_connection",
        help=argparse.SUPPRESS
    )
    follow_http_group = http_group.add_mutually_exclusive_group(required=False)
    follow_http_group.add_argument(
        "--follow",
        default=Config.allow_redirects,
        action="store_true",
        dest="allow_redirects",
        help="Follow 30x Location redirects (default: %(default)s)"
    )
    follow_http_group.add_argument(
        "--no-follow",
        action="store_false",
        dest="allow_redirects",
        help=argparse.SUPPRESS
    )
    user_agent_http_group = http_group.add_mutually_exclusive_group(required=False)
    user_agent_http_group.add_argument(
        "-ua", "--user-agent",
        default=Config.user_agent,
        help="Use a custom User-Agent (default: %(default)s)"
    )
    user_agent_http_group.add_argument(
        "-r", "--random-agent",
        dest="use_random_agent",
        action="store_true",
        help="Use a random valid browser User-Agent"
    )
    body_params_http_group = http_group.add_mutually_exclusive_group(required=False)
    body_params_http_group.add_argument(
        "-j", "--json",
        dest="use_json",
        action="store_true",
        default=Config.use_json,
        help="Data items from the command line are serialized as a JSON object (default: %(default)s)"
    )
    body_params_http_group.add_argument(
        "-f", "--form",
        dest="use_json",
        action="store_false",
        help="Data items from the command line are serialized as form fields"
    )
    http_group.add_argument(
        "--data-raw",
        dest="raw_data",
        help="Specify raw data to be sent as is (both as form fields or as JSON object)"
    )

    # Logging
    log_group = parser.add_argument_group(title="Logging")
    log_group.add_argument(
        "--log",
        dest="log_level",
        choices=["critical", "error", "warning", "info", "debug"],
        default=Config.log_level,
        help="To specify the log messages level"
    )

    # Input/Output scripts
    scripts_group = parser.add_argument_group(title="Input/Output scripts")
    scripts_group.add_argument(
        "--list-scripts",
        action="store_true",
        help="List the available scripts to manipulate input/output"
    )

    scripts_group.add_argument(
        "--input-scripts",
        dest="input_scripts",
        default=[],
        type=validators.input_scripts_chain,
        help="Use one or more custom input script (comma separated, order matters)"
    )

    scripts_group.add_argument(
        "--output-scripts",
        dest="output_scripts",
        default=[],
        type=validators.output_scripts_chain,
        help="Use one or more custom output script (comma separated, order matters)"
    )

    # Automatic updates
    update_group = parser.add_argument_group(title='Automatic updates')
    enable_update_group = update_group.add_mutually_exclusive_group(required=False)
    enable_update_group.add_argument(
        "--update",
        dest="check_for_updates",
        action="store_true",
        default=Config.check_for_updates,
        help="Check for updates on startup (default: %(default)s)"
    )
    enable_update_group.add_argument(
        "--no-update",
        dest="check_for_updates",
        action="store_false",
        help=argparse.SUPPRESS
    )
    prerelease_update_group = update_group.add_mutually_exclusive_group(required=False)
    prerelease_update_group.add_argument(
        "--include-prerelease",
        action="store_true",
        default=Config.include_prerelease,
        help="Includes pre-release while searching for updates (default: %(default)s)"
    )
    prerelease_update_group.add_argument(
        "--no-include-prerelease",
        dest="include_prerelease",
        action="store_false",
        help=argparse.SUPPRESS
    )

    # Positional parameters
    parser.add_argument(
        "url",
        metavar="URL",
        type=validators.http_url,
        help="The endpoint URL where the injection is"
    )
    parser.add_argument(
        "request_items",
        metavar="REQUEST ITEMS",
        nargs=argparse.ZERO_OR_MORE,
        default=[],
        help="POST data and headers ('key=value' for data, 'key:value' for headers)"
    )

    # Note: argparse is not flexible enough to have an argument with precedence over
    #       required positional arguments, so we have to check manually
    if "-h" not in args and "--help" not in args:
        if "--list-scripts" in args:
            print_scripts_list()
            sys.exit(os.EX_OK)

    return parser.parse_intermixed_args(args=args)


def print_scripts_list() -> None:
    """Prints the available input/output scripts."""
    for script_type, scripts in [("Input scripts", input_scripts), ("Output scripts", output_scripts)]:
        print(f"{script_type}:")
        for script_name, func in scripts.items():
            print(f"  {script_name} - {func.__doc__}")
        print()