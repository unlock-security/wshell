"""
WShell configuration module.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import urllib.parse
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from urllib.parse import urlparse

import wshell.constants
from wshell.enums import OSEnum
from wshell.http.data import to_nested_dictionary
from wshell.log import logger
from wshell.status import ExitStatus


@dataclass
class Config:
    """ Holds all runtime configuration for WShell. """
    # Application settings
    history_file: str

    # Core injection parameters
    url: str
    method: str
    command_placeholder: str = "WSHELL"

    # Logging settings
    log_level: str = "warning"

    # HTTP settings
    headers: Dict[str, str] = field(default_factory=dict)
    body_params: Dict = field(default_factory=dict)
    use_json: bool = False
    timeout: Optional[float] = 3.0
    delay: float = 0.0
    reuse_connection: bool = True
    allow_redirects: bool = True
    user_agent: str = f"WShell {wshell.constants.VERSION}"

    # Target OS
    os: Optional[OSEnum] = None

    # Scripts
    input_scripts: List[Callable[[str], str]] = field(default_factory=list)
    output_scripts: List[Callable[[str], str]] = field(default_factory=list)

    # Update settings
    check_for_updates: bool = True
    include_prerelease: bool = False


    @staticmethod
    def from_args(args: argparse.Namespace) -> Config:
        """Builds the final Config object from parsed arguments."""

        if args.use_random_agent:
            with open(wshell.constants.USER_AGENT_FILEPATH, "r") as f:
                args.user_agent = random.choice(
                    [line for line in f.read().splitlines() if line and not line.startswith("#")]
                )

        body_param_regex = re.compile(r"(?P<key>[\w\-.]+(\[\w*\])*)=(?P<value>.*)")
        headers_regex = re.compile(r"(?P<key>[\w\-.]+):\s*(?P<value>.*)")

        body_params = {}
        headers = {}

        for item in args.request_items:
            if match := body_param_regex.match(item):
                body_params[match.group('key')] = match.group('value')
            elif match := headers_regex.match(item):
                headers[match.group('key')] = match.group('value')
            else:
                # This should ideally be handled by argparse, but as a fallback:
                logger.error(f"Unrecognized argument: {item}")
                sys.exit(ExitStatus.GENERIC_ERROR)

        if args.use_json:
            body_params = to_nested_dictionary(body_params)

        if args.raw_data:
            raw_data_dict = json.loads(args.raw_data) if args.use_json else \
                            dict(urllib.parse.parse_qsl(args.raw_data, keep_blank_values=True))

            if isinstance(body_params, dict) and isinstance(raw_data_dict, dict):
                body_params.update(raw_data_dict)
            elif not body_params and raw_data_dict:
                body_params = raw_data_dict

        method = args.method or ("POST" if body_params else "GET")
        if not args.method:
            logger.info(f"HTTP verb not specified. Using '{method}' based on parameters")

        host = urlparse(args.url).hostname
        history_file = os.path.join(wshell.constants.USER_HISTORY_DIR, f"{host}.json")

        return Config(
            url=args.url,
            method=method,
            command_placeholder=args.command_placeholder,
            headers=headers,
            body_params=body_params,
            use_json=args.use_json,
            timeout=args.timeout,
            delay=args.delay,
            reuse_connection=args.reuse_connection,
            allow_redirects=args.allow_redirects,
            user_agent=args.user_agent,
            os=args.os,
            input_scripts=args.input_scripts,
            output_scripts=args.output_scripts,
            log_level=args.log_level.upper(),
            history_file=history_file,
            check_for_updates=args.check_for_updates,
            include_prerelease=args.include_prerelease
        )