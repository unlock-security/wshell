import importlib.metadata
import shutil
import subprocess
from typing import Optional

import requests
from packaging.version import InvalidVersion, Version

import wshell
import wshell.constants
from wshell.log import logger


class Updater:

    def __init__(self, include_prerelease: bool = False):
        self.include_prerelease = include_prerelease
        self.installer = None
        self.is_local = None
        self.is_editable = False
        self.origin_url = None        

        dist = importlib.metadata.distribution(wshell.__name__)
        if installer := dist.read_text("INSTALLER"):
            self.installer = installer.strip()

        if origin := dist.origin:
            self.origin_url = origin.url
            self.is_local = self.origin_url.startswith("file:")
            # only local packages can be editable
            if self.is_local:
                self.is_editable = getattr(origin.dir_info, "editable", False)

    def _fetch_latest_version(self) -> Optional[tuple[Version, str]]:
        response = requests.get(
            url=wshell.constants.GITHUB_RELEASES_URL,
            headers={"Accept": "application/vnd.github.v3+json"}
        )

        if response.status_code != 200:
            logger.error("Failed to fetch latest version number.")
            logger.debug(f"HTTP status code {response.status_code}: {response.text}")
            return None

        try:
            version_list = response.json()
            for version in version_list:
                if version["prerelease"] == self.include_prerelease:
                    return Version(version["tag_name"]), version["tag_name"]

            if not self.include_prerelease:
                logger.warning("No stable version found. Try including prereleases.")

        except InvalidVersion as e:
            logger.error("Failed to parse latest version number.")
            logger.debug(e)
        
        return None


    def update(self) -> bool:
        if self.is_editable or self.is_local:
            logger.warning("Installed as local or editable package. Skipping auto-update.")
            return False

        if ver := self._fetch_latest_version():
            latest_version, tag_name = ver
        else:
            logger.error("Failed to fetch latest version number. Skipping auto-update.")
            return False

        if latest_version <= wshell.constants.VERSION:
            logger.info(f"Latest version already installed: {wshell.constants.VERSION}")
            return False

        logger.warning(f"Newer version available: {wshell.constants.VERSION} → {latest_version}. Running update routine…")

        if not self.installer:
            logger.error("Unable to determine installer. Please, update manually.")
            return False

        # Packages installed via pipx have pip as installer, need to check manually
        if self.installer == "pip" and shutil.which("pipx") is not None:
                pipx_list_proc = subprocess.run(["pipx", "list", "--short"], capture_output=True)
                for package in pipx_list_proc.stdout.splitlines():
                    if package.decode().startswith(f"{wshell.__name__} "):
                        self.installer = "pipx"
                        break

        return self._run_upgrade(self.installer, tag_name)

    def _run_upgrade(self, package_manager: str, tag_name: str) -> bool:

        versioned_url = f"{self.origin_url}@{tag_name}"

        PACKAGE_MANAGERS_COMMANDS = {
            "pip": ["pip", "install", "--upgrade", versioned_url],
            "pipx": ["pipx", "install", "--foce", versioned_url],
            "uv": ["uv", "tool", "install", "--upgrade", versioned_url],
        }

        if package_manager not in PACKAGE_MANAGERS_COMMANDS:
            logger.error(f"Unsupported package manager '{package_manager}'. Please, update manually.")
            return False

        logger.info(f"Running update via {package_manager}")
        return subprocess.run(PACKAGE_MANAGERS_COMMANDS[package_manager]).returncode == 0