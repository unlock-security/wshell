from binascii import Error as BinasciiError
from typing import override

from cmd2 import Cmd

from wshell import utils
from wshell.commands import WShellCommandSet


class Base64PrintFileCommandSet(WShellCommandSet):
    """
    Overwrite `cat` (in Linux and Windows PSH) and `type` (in Windows CMD) to get file content
    as base64 to avoid some issues when manipulating the output (eg. escape \n)
    """

    @override
    def on_register(self, cmd: Cmd) -> None:
        super().on_register(cmd)
        if cmd.injector.is_windows_cmd():
            setattr(cmd, "do_type", self.get_file_content)
            cmd.hidden_commands.append("type")
        else:
            setattr(cmd, "do_cat", self.get_file_content)
            cmd.hidden_commands.append("cat")

    def get_file_content(self, filename: str):
        """
        Get the base64-encoded content of a file, decode it, and print it to the console.
        """
        base64_output = self._dispatch("get_base64_encoded_file", filename)
        try:
            self._cmd.poutput(utils.base64_decode(base64_output))
        except BinasciiError:
            self._cmd.perror(base64_output)

    def _linux_get_base64_encoded_file(self, filename: str) -> str:
        return self._cmd.injector.execute(f"base64 {filename} 2>&1")

    def _win_psh_get_base64_encoded_file(self, filename: str) -> str:
        return self._cmd.injector.execute(f"[System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content {filename})))")

    def _win_cmd_get_base64_encoded_file(self, filename: str) -> str:
        temp_filename = f"%TEMP%/{utils.random_string()}"
        return self._cmd.injector.execute(
            f"certutil -encodehex -f {filename} {temp_filename} 0x40000001>nul&& \
            type {temp_filename} && \
            del {temp_filename}"
        )