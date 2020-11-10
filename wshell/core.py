import argparse
import logging
import os
import random
import re
import requests
import requests.utils
import sys
from typing import List, Union

import wshell
from wshell import validators, settings
from wshell.cli import WShellCmd
from wshell.errors import WShellError
from wshell.injectors import OSEnum, get_command_injector
from wshell.log import logger
from wshell.status import ExitStatus


# noinspection PyDefaultArgument
def main(args: List[Union[str, bytes]] = sys.argv) -> ExitStatus:
    """
    Process arguments and run the main workflow.
    :param args list of command line arguments to parse
    :return exit status code.
    """
    # remove program name from args to not be confused as positional argument
    program_name, *args = args

    parser = argparse.ArgumentParser(
        prog="wshell",
        description="Turn a web-based {code,command,template} injection in a full featured shell with ease",
        epilog='For every --ARGUMENT there is also a --no-ARGUMENT that reverts ARGUMENT',
        add_help=True,
        allow_abbrev=False
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s v{wshell.__version__}",
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
        choices=[_os.value for _os in OSEnum.__members__.values()],
        help="Specify OS and shell in use on the target (default: auto-discover)"
    )

    # HTTP-related parameters
    http_group = parser.add_argument_group(title='HTTP arguments')
    parser.add_argument(
        "-m", "--method",
        help="The HTTP method to be used for the requests (Default: POST if there is some data, GET otherwise)"
    )
    http_group.add_argument(
        "-t", "--timeout",
        metavar="SECONDS",
        type=validators.positive_float,
        default=settings.DEFAULT_TIMEOUT,
        help='The connection timeout of the request in seconds (default: %(default)s)'
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

    log_group = parser.add_argument_group(title="Logging arguments")
    log_group.add_argument(
        "--log",
        dest="log_level",
        choices=["critical", "error", "warning", "info", "debug"],
        default=settings.DEFAULT_LOG_LEVEL,
        help="To specify the log messages level"
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

    parsed_args = parser.parse_intermixed_args(args=args)

    # Specify the log level to the WShell root logger
    logger.setLevel(logging.getLevelName(parsed_args.log_level.upper()))

    if parsed_args.use_random_agent:
        # Pick a random user-agent excluding empty and comment lines
        with open(os.path.join(wshell.DATA_DIR, "user-agents.txt"), "r") as f:
            parsed_args.user_agent = random.choice(
                [line for line in f.read().splitlines() if line and not line.startswith("#")]
            )

    requests.utils.default_user_agent = lambda: parsed_args.user_agent

    # Parse positional arguments to extract POST data and headers
    post_data_regex = re.compile(r"(?P<key>[\w\-.]+)=(?P<value>.*)")  # POST data are in the form "key=value"
    headers_regex = re.compile(r"(?P<key>[\w\-.]+):(?P<value>.*)")  # HTTP headers are in the form "key:value"

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

    # Replace raw request items with parsed ones
    del parsed_args.request_items
    parsed_args.post_data = post_data
    parsed_args.headers = headers

    if not parsed_args.method:
        parsed_args.method = "POST" if post_data else "GET"
        logger.info(f"HTTP verb not specified. Using '{parsed_args.method}' based on parameters")

    if parsed_args.os:
        parsed_args.os = OSEnum(parsed_args.os)

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
            reuse_connection=args.reuse_connection,
            use_json_post_data=args.use_json_post_data,
            method=args.method,
            url=args.url,
            post_data=args.post_data,
            headers=args.headers,
            command_placeholder=args.command_placeholder
        )

        WShellCmd(
            injector=injector
        ).cmdloop()
    except WShellError as error:
        logger.error(f"{error.__class__.__name__}: {error}")
        return error.EXIT_STATUS

    return ExitStatus.SUCCESS
