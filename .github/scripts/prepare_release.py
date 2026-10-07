"""Plan a stable release from reachable tags and Conventional Commit messages."""

import argparse
import os
import re
import subprocess
from pathlib import Path

from packaging.version import InvalidVersion, Version

ROOT = Path(__file__).resolve().parents[2]
VERSION_ASSIGNMENT = re.compile(
    r"^(__version__\s*=\s*)([\"'])([^\"']+)\2[ \t]*$", re.MULTILINE
)
COMMIT_HEADER = re.compile(r"^([a-z]+)(?:\([^\n)]+\))?(!)?: .+", re.IGNORECASE)
BREAKING_FOOTER = re.compile(r"^BREAKING[ -]CHANGE: .+", re.MULTILINE)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def release_tags(tags: list[str]) -> list[tuple[Version, str]]:
    releases = []
    for tag in tags:
        if not tag.startswith("v"):
            continue
        try:
            version = Version(tag)
        except InvalidVersion:
            continue
        if len(version.release) == 3 and not (
            version.is_devrelease or version.is_postrelease or version.local or version.epoch
        ):
            releases.append((version, tag))
    return sorted(releases, reverse=True)


def bump_level(messages: list[str]) -> int:
    """Return 0 for no release, 1 for patch, 2 for minor, or 3 for major."""
    level = 0
    for message in messages:
        header = COMMIT_HEADER.match(message.strip())
        if not header:
            continue
        if header[2] or BREAKING_FOOTER.search(message):
            return 3
        kind = header[1].lower()
        level = max(level, 2 if kind == "feat" else 1 if kind in {"fix", "perf"} else 0)
    return level


def next_version(base: Version, messages: list[str]) -> Version | None:
    level = bump_level(messages)
    major, minor, patch = base.release
    if level == 3:
        return Version(f"{major + 1}.0.0")
    if level == 2:
        return Version(f"{major}.{minor + 1}.0")
    if level == 1:
        return Version(f"{major}.{minor}.{patch + 1}")
    return None


def prepare_release(*, dry_run: bool = False) -> dict[str, str]:
    version_file = ROOT / "wshell" / "__init__.py"
    content = version_file.read_text()
    assignments = list(VERSION_ASSIGNMENT.finditer(content))
    if len(assignments) != 1:
        raise ValueError("Expected one __version__ assignment in wshell/__init__.py")
    current = Version(assignments[0][3])
    tags = release_tags(git("tag", "--merged", "HEAD").splitlines())
    stable_tags = [(version, tag) for version, tag in tags if not version.is_prerelease]
    previous_tag = stable_tags[0][1] if stable_tags else tags[0][1] if tags else ""
    outputs = {"commit": "false", "tag": "", "version": "", "previous_tag": previous_tag}

    if stable_tags:
        base, latest_tag = stable_tags[0]
        # A rerun after tagging must finish publication instead of bumping again.
        if git("rev-parse", f"{latest_tag}^{{commit}}") == git("rev-parse", "HEAD"):
            if current != base:
                raise ValueError("The tagged version does not match wshell/__init__.py")
            earlier_tags = [(version, tag) for version, tag in tags if version < base]
            outputs.update(
                tag=latest_tag,
                version=str(base),
                previous_tag=earlier_tags[0][1] if earlier_tags else "",
            )
            return outputs
        messages = git("log", "--format=%B%x00", f"{latest_tag}..HEAD").split("\0")
        version = next_version(base, messages)
    else:
        # Promote the existing beta line to its first stable release.
        base = max([current, *(version for version, _ in tags)])
        version = Version(".".join(map(str, base.release)))

    if version is None:
        return outputs
    tag = f"v{version}"
    if tag in git("tag", "--list").splitlines():
        raise ValueError(f"Release tag {tag} already exists outside this release history")
    if not dry_run:
        version_file.write_text(
            VERSION_ASSIGNMENT.sub(lambda match: f'{match[1]}"{version}"', content)
        )
    outputs.update(commit="true", tag=tag, version=str(version))
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Plan without changing files")
    args = parser.parse_args()
    outputs = prepare_release(dry_run=args.dry_run)
    report = "".join(f"{key}={value}\n" for key, value in outputs.items())
    print(report, end="")
    if output_file := os.environ.get("GITHUB_OUTPUT"):
        with open(output_file, "a") as stream:
            stream.write(report)


if __name__ == "__main__":
    main()
