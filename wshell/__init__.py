"""
WShell: Turn a web-based {code,command,template} injection in a full featured shell with ease.
"""

import importlib.metadata
import os

import platformdirs
from packaging.version import Version

import wshell

VERSION = Version(importlib.metadata.version(wshell.__name__))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

USER_DATA_DIR = platformdirs.user_data_dir(wshell.__name__)
USER_HISTORY_DIR = os.path.join(USER_DATA_DIR, 'history')

GITHUB_RELEASES_URL = "https://api.github.com/repos/unlock-security/wshell/releases"