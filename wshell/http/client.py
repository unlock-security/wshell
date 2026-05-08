"""
HTTP Client for WShell.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

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
        self.allow_redirects = config.allow_redirects
        self.timeout = config.timeout
        self.delay = config.delay
        
        requests.utils.default_user_agent = lambda: config.user_agent

    def send_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Sends an HTTP request.
        """
        time.sleep(self.delay)

        try:
            response = self.http.request(
                method,
                url,
                headers=headers,
                data=data,
                json=json,
                allow_redirects=self.allow_redirects,
                timeout=self.timeout,
                verify=False # This is a post-exploitation tool, we don't care about unverified SSL certs
            )
            return response
        except requests.exceptions.ConnectionError as err:
            raise TargetUnreachableError from err
