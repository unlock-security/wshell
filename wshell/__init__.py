"""
WShell: Turn a web-based {code,command,template} injection in a full featured shell with ease.
"""

import importlib.metadata
import os

from packaging.version import Version

import wshell

VERSION = Version(importlib.metadata.version(wshell.__name__))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')