from __future__ import annotations

import importlib.metadata
import shutil
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

import requests
from packaging.version import InvalidVersion, Version

import wshell
import wshell.constants
from wshell.log import logger


@dataclass(frozen=True)
class InstallationInfo:
    installer: str | None
    origin_url: str | None
    is_local: bool
    is_editable: bool


@dataclass(frozen=True)
class ReleaseInfo:
    version: Version
    tag_name: str


class ReleaseFetcher(Protocol):
    def fetch(self, *, include_prerelease: bool) -> ReleaseInfo | None: ...


class CommandRunner(Protocol):
    def run(self, command: list[str]) -> bool: ...


class GitHubReleaseFetcher:
    """Fetch release metadata from GitHub."""

    def fetch(self, *, include_prerelease: bool) -> ReleaseInfo | None:
        response = requests.get(
            url=wshell.constants.GITHUB_RELEASES_URL,
            headers={"Accept": "application/vnd.github.v3+json"},
        )

        if response.status_code != 200:
            logger.error("Failed to fetch latest version number.")
            logger.debug(f"HTTP status code {response.status_code}: {response.text}")
            return None

        try:
            release = select_release(response.json(), include_prerelease=include_prerelease)
            if release is not None:
                return release
            if not include_prerelease:
                logger.warning("No stable version found. Try including prereleases.")
        except InvalidVersion as error:
            logger.error("Failed to parse latest version number.")
            logger.debug(error)

        return None


class SubprocessCommandRunner:
    """Run upgrade commands in subprocesses."""

    def run(self, command: list[str]) -> bool:
        return subprocess.run(command, shell=False).returncode == 0


class Updater:
    """Resolve installation metadata and run self-updates when appropriate."""

    def __init__(
        self,
        include_prerelease: bool = False,
        *,
        release_fetcher: ReleaseFetcher | None = None,
        command_runner: CommandRunner | None = None,
    ):
        self.include_prerelease = include_prerelease
        self.release_fetcher = release_fetcher or GitHubReleaseFetcher()
        self.command_runner = command_runner or SubprocessCommandRunner()
        self.installation = self._read_installation_info()

    def _read_installation_info(self) -> InstallationInfo:
        dist = importlib.metadata.distribution(wshell.__name__)
        installer = dist.read_text("INSTALLER")
        origin = getattr(dist, "origin", None)
        origin_url = getattr(origin, "url", None)
        is_local = bool(origin_url and origin_url.startswith("file:"))
        is_editable = bool(
            is_local and getattr(getattr(origin, "dir_info", None), "editable", False)
        )
        return InstallationInfo(
            installer=installer.strip() if installer else None,
            origin_url=origin_url,
            is_local=is_local,
            is_editable=is_editable,
        )

    def update(self) -> bool:
        if self.installation.is_editable or self.installation.is_local:
            logger.warning("Installed as local or editable package. Skipping auto-update.")
            return False

        release = self.release_fetcher.fetch(include_prerelease=self.include_prerelease)
        if release is None:
            logger.error("Failed to fetch latest version number. Skipping auto-update.")
            return False

        if release.version <= wshell.constants.VERSION:
            logger.info(f"Latest version already installed: {wshell.constants.VERSION}")
            return False

        logger.warning(
            f"Newer version available: {wshell.constants.VERSION} → {release.version}. Running update routine…"
        )

        installer = self.detect_installer(self.installation.installer)
        if installer is None:
            logger.error("Unable to determine installer. Please, update manually.")
            return False

        command = build_upgrade_command(installer, self.installation.origin_url, release.tag_name)
        if command is None:
            logger.error(f"Unsupported package manager '{installer}'. Please, update manually.")
            return False

        logger.info(f"Running update via {installer}")
        return self.command_runner.run(command)

    def detect_installer(self, installer: str | None) -> str | None:
        """Resolve the effective package manager used for this installation."""

        if installer != "pip" or shutil.which("pipx") is None:
            return installer

        pipx_list_proc = subprocess.run(["pipx", "list", "--short"], capture_output=True, text=True)
        for package in pipx_list_proc.stdout.splitlines():
            if package.startswith(f"{wshell.__name__} "):
                return "pipx"
        return installer


def build_upgrade_command(
    package_manager: str, origin_url: str | None, tag_name: str
) -> list[str] | None:
    """Return the self-upgrade command for the selected package manager."""

    if not origin_url:
        return None

    versioned_url = f"{origin_url}@{tag_name}"
    commands = {
        "pip": ["pip", "install", "--upgrade", versioned_url],
        "pipx": ["pipx", "install", "--force", versioned_url],
        "uv": ["uv", "tool", "install", "--upgrade", versioned_url],
    }
    return commands.get(package_manager)


def select_release(
    releases: Iterable[dict[str, object]], *, include_prerelease: bool
) -> ReleaseInfo | None:
    """Select the first release matching prerelease policy."""

    for release in releases:
        if release.get("prerelease") != include_prerelease:
            continue
        tag_name = release.get("tag_name")
        if not isinstance(tag_name, str):
            continue
        try:
            return ReleaseInfo(version=Version(tag_name), tag_name=tag_name)
        except InvalidVersion:
            continue
    return None
