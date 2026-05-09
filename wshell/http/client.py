"""
HTTP Client for WShell.
"""

from __future__ import annotations

import time
from typing import Any

import requests
import urllib3

from wshell.config import Config
from wshell.errors import TargetUnreachableError, TimeoutExpiredError
from wshell.http.tracing import (
    render_request_trace,
    render_response_trace,
)
from wshell.log import logger

# Disable warnings related to unverified SSL certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HttpClient:
    """
    A dedicated HTTP client for WShell, encapsulating requests logic.
    """

    def __init__(self, config: Config):
        self.session = requests.Session() if config.reuse_connection else None
        self.user_agent = config.user_agent
        self.allow_redirects = config.allow_redirects
        self.timeout = config.timeout
        self.delay = config.delay

    def send_request(
        self,
        trace_id: str,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> requests.Response:
        """
        Sends an HTTP request.
        """
        time.sleep(self.delay)
        request_headers = dict(headers or {})
        request_headers.setdefault("User-Agent", self.user_agent)
        prepared_request = self._prepare_request(
            method=method,
            url=url,
            headers=request_headers,
            data=data,
            json=json,
        )

        logger.debug("%s", render_request_trace(prepared_request, trace_id))

        try:
            start_time = time.perf_counter()
            response = self._send_prepared_request(prepared_request)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.debug("%s", render_response_trace(response, trace_id, elapsed_ms))
            return response
        except requests.exceptions.ConnectionError as err:
            raise TargetUnreachableError(err) from err
        except requests.exceptions.ReadTimeout as err:
            raise TimeoutExpiredError(err) from err

    def _prepare_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        data: dict[str, Any] | None,
        json: dict[str, Any] | None,
    ) -> requests.PreparedRequest:
        request = requests.Request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            json=json,
        )

        if self.session:
            return self.session.prepare_request(request)

        return request.prepare()

    def _send_prepared_request(self, request: requests.PreparedRequest) -> requests.Response:
        send_kwargs = {
            "allow_redirects": self.allow_redirects,
            "timeout": self.timeout,
            # This is a post-exploitation tool, we don't care about unverified SSL certs.
            "verify": False,
        }

        if self.session:
            return self.session.send(request, **send_kwargs)

        # Create a new session for each request
        with requests.Session() as session:
            return session.send(request, **send_kwargs)
