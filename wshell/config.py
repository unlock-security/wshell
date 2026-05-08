"""WShell runtime configuration helpers."""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import wshell.constants
from wshell.enums import OSEnum
from wshell.errors import InvalidRequestItemError
from wshell.http.data import to_nested_dictionary

BODY_PARAM_REGEX = re.compile(r"(?P<key>[\w\-.]+(\[\w*\])*)=(?P<value>.*)")
HEADER_REGEX = re.compile(r"(?P<key>[\w\-.]+):\s*(?P<value>.*)")


@dataclass(frozen=True)
class RequestSpec:
    """HTTP request shape used for command injection."""

    url: str
    method: str
    headers: dict[str, str] = field(default_factory=dict)
    body_params: dict[str, Any] = field(default_factory=dict)
    use_json: bool = False


@dataclass(frozen=True)
class Config:
    """Holds all runtime configuration for WShell."""

    history_file: str
    request: RequestSpec

    command_placeholder: str = "WSHELL"
    prompt: str | None = None
    log_level: str = "warning"
    timeout: float | None = 3.0
    delay: float = 0.0
    reuse_connection: bool = True
    allow_redirects: bool = True
    user_agent: str = f"WShell {wshell.constants.VERSION}"
    os: OSEnum | None = None
    input_scripts: list[Callable[[str], str]] = field(default_factory=list)
    output_scripts: list[Callable[[str], str]] = field(default_factory=list)
    check_for_updates: bool = True
    include_prerelease: bool = False

    @property
    def url(self) -> str:
        return self.request.url

    @property
    def method(self) -> str:
        return self.request.method

    @property
    def headers(self) -> dict[str, str]:
        return self.request.headers

    @property
    def body_params(self) -> dict[str, Any]:
        return self.request.body_params

    @property
    def use_json(self) -> bool:
        return self.request.use_json

    @staticmethod
    def from_args(args: argparse.Namespace) -> Config:
        """Build the final immutable runtime configuration from parsed arguments."""

        request_items = parse_request_items(args.request_items, use_json=args.use_json)
        body_params = merge_raw_data(
            base_body=request_items.body_params,
            raw_data=args.raw_data,
            use_json=args.use_json,
        )
        request = RequestSpec(
            url=args.url,
            method=infer_http_method(args.method, body_params),
            headers=request_items.headers,
            body_params=body_params,
            use_json=args.use_json,
        )
        return Config(
            history_file=build_history_path(args.url),
            request=request,
            command_placeholder=args.command_placeholder,
            prompt=args.prompt,
            log_level=args.log_level.upper(),
            timeout=args.timeout,
            delay=args.delay,
            reuse_connection=args.reuse_connection,
            allow_redirects=args.allow_redirects,
            user_agent=resolve_user_agent(args.user_agent, args.use_random_agent),
            os=args.os,
            input_scripts=args.input_scripts,
            output_scripts=args.output_scripts,
            check_for_updates=args.check_for_updates,
            include_prerelease=args.include_prerelease,
        )


@dataclass(frozen=True)
class ParsedRequestItems:
    """Header and body items parsed from the CLI."""

    headers: dict[str, str] = field(default_factory=dict)
    body_params: dict[str, str] = field(default_factory=dict)


def parse_request_items(items: list[str], *, use_json: bool) -> ParsedRequestItems:
    """Parse CLI request items into structured headers and body parameters."""

    headers: dict[str, str] = {}
    body_params: dict[str, str] = {}

    for item in items:
        if match := BODY_PARAM_REGEX.match(item):
            body_params[match.group("key")] = match.group("value")
            continue
        if match := HEADER_REGEX.match(item):
            headers[match.group("key")] = match.group("value")
            continue
        raise InvalidRequestItemError(f"Unrecognized request item: {item}")

    if use_json:
        return ParsedRequestItems(headers=headers, body_params=to_nested_dictionary(body_params))
    return ParsedRequestItems(headers=headers, body_params=body_params)


def merge_raw_data(
    *, base_body: dict[str, Any], raw_data: str | None, use_json: bool
) -> dict[str, Any]:
    """Merge request items with optional raw body data."""

    if not raw_data:
        return base_body

    raw_body = parse_raw_data(raw_data, use_json=use_json)
    if isinstance(base_body, dict) and isinstance(raw_body, dict):
        return {**base_body, **raw_body}
    if not base_body and isinstance(raw_body, dict):
        return raw_body
    return base_body


def parse_raw_data(raw_data: str, *, use_json: bool) -> dict[str, Any]:
    """Parse `--data-raw` as either JSON or form-urlencoded data."""

    if use_json:
        parsed = json.loads(raw_data)
        if not isinstance(parsed, dict):
            raise InvalidRequestItemError("--data-raw JSON payload must be an object")
        return parsed
    return dict(urllib.parse.parse_qsl(raw_data, keep_blank_values=True))


def infer_http_method(method: str | None, body_params: dict[str, Any]) -> str:
    """Infer the request method if the user did not specify one."""

    return method or ("POST" if body_params else "GET")


def build_history_path(url: str) -> str:
    """Return the per-host history file path."""

    host = urlparse(url).hostname or "wshell"
    return os.path.join(wshell.constants.USER_HISTORY_DIR, f"{host}.json")


def resolve_user_agent(user_agent: str, use_random_agent: bool) -> str:
    """Return the effective user agent string."""

    if not use_random_agent:
        return user_agent

    with open(wshell.constants.USER_AGENT_FILEPATH, encoding="utf-8") as handle:
        return random.choice(
            [line for line in handle.read().splitlines() if line and not line.startswith("#")]
        )
