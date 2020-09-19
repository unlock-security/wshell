import errno
import json
import os
from pathlib import Path
from typing import Union


ENV_XDG_CONFIG_HOME = 'XDG_CONFIG_HOME'
ENV_WSHELL_CONFIG_DIR = 'WSHELL_CONFIG_DIR'
DEFAULT_CONFIG_DIRNAME = 'wshell'
DEFAULT_RELATIVE_XDG_CONFIG_HOME = Path('.config')
DEFAULT_RELATIVE_LEGACY_CONFIG_DIR = Path('.wshell')


def get_default_config_dir() -> Path:
    """ Return the path to the wshell configuration directory.

    The priority is:

    - "WSHELL_CONFIG_DIR" environment variable
    - Legacy ~/.wshell
    - XDG (defaults to $HOME/.config/ if not specified differently by "XDG_CONFIG_HOME" environment variable)

    NOTE: This directory isn't guaranteed to exist, and nor are any of its
    ancestors (only the legacy ~/.wshell, if returned, is guaranteed to exist).
    """
    # Case 1. explicitly set through env
    env_config_dir = os.environ.get(ENV_WSHELL_CONFIG_DIR)
    if env_config_dir:
        return Path(env_config_dir)

    home_dir = Path.home()

    # Case 2. legacy ~/.wshell
    legacy_config_dir = home_dir / DEFAULT_RELATIVE_LEGACY_CONFIG_DIR
    if legacy_config_dir.exists():
        return legacy_config_dir

    # 4. XDG
    xdg_config_home_dir = os.environ.get(
        ENV_XDG_CONFIG_HOME,  # 4.1. explicit
        home_dir / DEFAULT_RELATIVE_XDG_CONFIG_HOME  # 4.2. default
    )
    return Path(xdg_config_home_dir) / DEFAULT_CONFIG_DIRNAME


DEFAULT_CONFIG_DIR = get_default_config_dir()


class ConfigFileError(Exception):
    """ An error occurred trying to read/write/parse configuration file"""


class BaseConfigDict(dict):
    def __init__(self, path: Path):
        super().__init__()
        self.config_path = path

    def load(self):
        """ Load options from configuration file """

        try:
            with self.config_path.open("rt") as f:
                try:
                    data = json.load(f)
                except ValueError as e:
                    raise ConfigFileError(f"Invalid configuration file: {e}")
                self.update(data)
        except OSError as e:
            raise ConfigFileError(f"Cannot read configuration file: {e.strerror}")

    def save(self) -> None:
        """ Save the configuration to file in JSON format
        :raise OSError: if it is not possible to create the config directory
        :raise IOError: if it is not possible to write to config file
        """

        try:
            self.config_path.parent.mkdir(mode=0o700, parents=True)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        json_string = json.dumps(
            obj=self,
            indent=4,
            sort_keys=True,
            ensure_ascii=True
        )
        self.config_path.write_text(json_string)


class Config(BaseConfigDict):
    FILENAME = "config.json"

    def __init__(self, file_path: Union[str, Path] = DEFAULT_CONFIG_DIR / FILENAME):
        if file_path:
            file_path = Path(file_path)
        super().__init__(path=file_path)
