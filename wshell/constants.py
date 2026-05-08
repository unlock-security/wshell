import os

import platformdirs
from packaging.version import Version

import wshell

VERSION = Version(wshell.__version__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
USER_AGENT_FILEPATH = os.path.join(DATA_DIR, "user-agents.txt")

USER_DATA_DIR = platformdirs.user_data_dir(wshell.__name__)
USER_HISTORY_DIR = os.path.join(USER_DATA_DIR, 'history')

GITHUB_RELEASES_URL = "https://api.github.com/repos/unlock-security/wshell/releases"