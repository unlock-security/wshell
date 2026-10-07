"""Exercise cmd2 integration without making requests to a target."""

import base64
import io
from unittest.mock import Mock

import pytest

from wshell.cmd import WShellCmd
from wshell.enums import OSEnum


@pytest.fixture(scope="module")
def shell():
    injector = Mock(timeout=10, OS=OSEnum.LINUX)
    injector.get_prompt.return_value = "remote> "
    injector.is_windows_cmd.return_value = False
    return WShellCmd(injector)


@pytest.fixture
def app(shell):
    shell.stdout = io.StringIO()
    shell.history.clear()
    shell.injector.reset_mock()
    shell.injector.execute.side_effect = None
    shell.injector.execute.return_value = "remote output"
    return shell


@pytest.mark.parametrize("command", ["upload", "download"])
def test_transfer_help(app, command, capsys):
    app.onecmd_plus_hooks(f"{command} --help")

    assert f"Usage: {command}" in app.stdout.getvalue()
    assert "--no-chunk" in app.stdout.getvalue()
    assert not capsys.readouterr().err
    app.injector.execute.assert_not_called()


def test_upload_parses_arguments_and_transfers_content(app, tmp_path, capsys):
    source = tmp_path / "local file.bin"
    content = b"\x00\xfftest\n"
    source.write_bytes(content)

    app.onecmd_plus_hooks(f'upload -l "{source}" -r remote.bin --no-chunk')

    app.injector.execute.assert_called_once()
    remote_command = app.injector.execute.call_args.args[0]
    assert base64.b64encode(content).decode() in remote_command
    assert "remote.bin" in remote_command
    assert not capsys.readouterr().err


@pytest.mark.parametrize("chunked", [False, True])
def test_download_parses_arguments_and_writes_content(app, tmp_path, chunked, capsys):
    destination = tmp_path / "downloaded file.bin"
    content = b"\x00\xfftest\n"
    if chunked:
        app.injector.execute.side_effect = [
            str(len(content)),
            base64.b64encode(content[:4]).decode(),
            base64.b64encode(content[4:]).decode(),
        ]
    else:
        app.injector.execute.return_value = base64.b64encode(content).decode()
    option = "--chunk 4" if chunked else "--no-chunk"

    app.onecmd_plus_hooks(f'download -r remote.bin -l "{destination}" {option}')

    assert destination.read_bytes() == content
    assert app.injector.execute.call_count == (3 if chunked else 1)
    assert not capsys.readouterr().err


def test_remote_command_preserves_redirection_and_history(app):
    command = "printf 'hello' > remote.txt | head"

    app.onecmd_plus_hooks(command)

    app.injector.execute.assert_called_once_with(cmd=command)
    assert "remote output" in app.stdout.getvalue()
    assert [item.raw for item in app.history] == [command]


def test_cd_updates_prompt(app):
    app.injector.change_directory.return_value = "/tmp"
    app.injector.get_prompt.return_value = "remote:/tmp> "

    app.onecmd_plus_hooks("cd /tmp")

    app.injector.change_directory.assert_called_once_with("/tmp")
    assert app.prompt == "remote:/tmp> "
    assert "/tmp" in app.stdout.getvalue()


def test_set_timeout(app):
    app.onecmd_plus_hooks("set timeout 12")

    assert app.injector.timeout == 12
    assert set(app.settables) == {"debug", "timing", "timeout"}
