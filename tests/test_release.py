"""Check version selection and release retries in disposable Git repositories."""

import runpy
import subprocess
from pathlib import Path

import pytest
from packaging.version import Version


@pytest.fixture(scope="module")
def release_script():
    return runpy.run_path(
        str(Path(__file__).resolve().parents[1] / ".github/scripts/prepare_release.py")
    )


@pytest.fixture
def repository(tmp_path, monkeypatch, release_script):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()

    git("init", "--initial-branch=main")
    git("config", "user.name", "Release Test")
    git("config", "user.email", "release-test@example.com")
    package = tmp_path / "wshell"
    package.mkdir()
    (package / "__init__.py").write_text('__version__ = "0.3.0b0"\n')
    git("add", ".")
    git("commit", "-m", "chore: bootstrap beta")
    git("tag", "v0.3.0-beta")
    monkeypatch.setitem(release_script["prepare_release"].__globals__, "ROOT", tmp_path)
    return tmp_path, git


@pytest.mark.parametrize(
    ("messages", "expected"),
    [
        (["fix: correct output"], "0.3.1"),
        (["FIX(parser): correct output"], "0.3.1"),
        (["perf: reduce requests"], "0.3.1"),
        (["feat: add upload", "fix: correct output"], "0.4.0"),
        (["feat(api)!: change interface"], "1.0.0"),
        (["chore!: drop Python support"], "1.0.0"),
        (["fix: update interface\n\nBREAKING CHANGE: remove old API"], "1.0.0"),
        (["feat: update interface\n\nBREAKING-CHANGE: remove old API"], "1.0.0"),
        (["docs: explain usage", "chore: update tooling", "Merge branch dev"], None),
    ],
)
def test_conventional_version_bumps(release_script, messages, expected):
    version = release_script["next_version"](Version("0.3.0"), messages)
    assert version == (Version(expected) if expected else None)


def test_first_stable_release_preserves_legacy_tags(repository, release_script):
    root, git = repository

    plan = release_script["prepare_release"]()

    assert plan == {
        "commit": "true", "tag": "v0.3.0", "version": "0.3.0",
        "previous_tag": "v0.3.0-beta",
    }
    assert (root / "wshell/__init__.py").read_text() == '__version__ = "0.3.0"\n'
    assert git("tag", "--list") == "v0.3.0-beta"


def test_dry_run_leaves_version_unchanged(repository, release_script):
    root, git = repository

    plan = release_script["prepare_release"](dry_run=True)

    assert plan["tag"] == "v0.3.0"
    assert not git("status", "--porcelain")
    assert (root / "wshell/__init__.py").read_text() == '__version__ = "0.3.0b0"\n'


def finish_release(git, tag):
    git("add", "wshell/__init__.py")
    git("commit", "-m", f"chore(release): {tag}")
    git("tag", "-a", tag, "-m", f"Release {tag}")


def test_release_retry_reuses_version_and_tag(repository, release_script):
    _, git = repository
    initial = release_script["prepare_release"]()
    finish_release(git, initial["tag"])

    plan = release_script["prepare_release"]()

    assert plan == initial | {"commit": "false"}
    assert not git("status", "--porcelain")


def test_subsequent_release_considers_only_new_commits(repository, release_script):
    root, git = repository
    initial = release_script["prepare_release"]()
    finish_release(git, initial["tag"])
    git("commit", "--allow-empty", "-m", "feat: add feature")
    feature = release_script["prepare_release"]()
    assert feature["tag"] == "v0.4.0"
    finish_release(git, feature["tag"])
    git("commit", "--allow-empty", "-m", "fix: correct feature")

    plan = release_script["prepare_release"]()

    assert plan["tag"] == "v0.4.1"
    assert plan["previous_tag"] == "v0.4.0"
    assert (root / "wshell/__init__.py").read_text() == '__version__ = "0.4.1"\n'


def test_docs_only_changes_skip_release(repository, release_script):
    _, git = repository
    initial = release_script["prepare_release"]()
    finish_release(git, initial["tag"])
    git("commit", "--allow-empty", "-m", "docs: clarify installation")

    plan = release_script["prepare_release"]()

    assert plan["commit"] == "false"
    assert plan["tag"] == ""
    assert not git("status", "--porcelain")


def test_unreachable_stable_tag_is_not_a_version_baseline(repository, release_script):
    _, git = repository
    git("checkout", "-b", "unmerged")
    git("commit", "--allow-empty", "-m", "feat: unreleased experiment")
    git("tag", "v9.0.0")
    git("checkout", "main")

    plan = release_script["prepare_release"](dry_run=True)

    assert plan["tag"] == "v0.3.0"


def test_conflicting_tag_fails_without_changing_version(repository, release_script):
    root, git = repository
    git("checkout", "-b", "unmerged")
    git("commit", "--allow-empty", "-m", "feat: unrelated release")
    git("tag", "v0.3.0")
    git("checkout", "main")

    with pytest.raises(ValueError, match="already exists"):
        release_script["prepare_release"]()

    assert (root / "wshell/__init__.py").read_text() == '__version__ = "0.3.0b0"\n'
