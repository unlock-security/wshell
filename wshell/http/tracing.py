"""HTTP debug trace rendering helpers."""

from collections.abc import ItemsView

import requests


def render_request_trace(request: requests.PreparedRequest, trace_id: str) -> str:
    """Render a prepared request as a multi-line debug block."""

    lines = [
        f"http#{trace_id} request",
        f"> {request.method} {request.url}",
        *_format_headers(request.headers.items(), prefix="> "),
        ">",
        *_format_body(request.body, prefix="> "),
    ]
    return "\n".join(lines)


def render_response_trace(response: requests.Response, trace_id: str) -> str:
    """Render a response as a multi-line debug block."""

    lines = [
        f"http#{trace_id} response",
        f"< HTTP {response.status_code} {response.reason}",
        *_format_headers(response.headers.items(), prefix="< "),
        "<",
        *_format_body(response.text, prefix="< "),
    ]
    return "\n".join(lines)


def _format_headers(headers: ItemsView[str, str], prefix: str) -> list[str]:
    items = list(headers)
    return [f"{prefix}{key}: {value}" for key, value in items]


def _format_body(body: bytes | str | None, prefix: str) -> list[str]:
    text = _coerce_body(body)
    return [f"{prefix}{line}" for line in text.splitlines()] or [prefix.rstrip()]


def _coerce_body(body: bytes | str | None) -> str:
    if body is None:
        return ""
    if isinstance(body, bytes):
        return body.decode("utf-8", errors="replace")
    return str(body)
