"""
HTTP Client for WShell.
"""

from __future__ import annotations

import time
from typing import Any

import requests
import urllib3

from wshell.config import Config
from wshell.errors import TargetUnreachableError

# Disable warnings related to unverified SSL certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HttpClient:
    """
    A dedicated HTTP client for WShell, encapsulating requests logic.
    """

    def __init__(self, config: Config):
        self.http = requests.Session() if config.reuse_connection else requests
        self.user_agent = config.user_agent
        self.allow_redirects = config.allow_redirects
        self.timeout = config.timeout
        self.delay = config.delay

        if isinstance(self.http, requests.Session):
            self.http.headers.update({"User-Agent": self.user_agent})

    def send_request(
        self,
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

        try:
            response = self.http.request(
                method,
                url,
                headers=request_headers,
                data=data,
                json=json,
                allow_redirects=self.allow_redirects,
                timeout=self.timeout,
                verify=False,  # This is a post-exploitation tool, we don't care about unverified SSL certs
            )
            return response
        except requests.exceptions.ConnectionError as err:
            raise TargetUnreachableError from err
