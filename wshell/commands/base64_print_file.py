from binascii import Error as BinasciiError
from typing import override

from cmd2 import Cmd

from wshell import utils
from wshell.commands import WshellCommandSet


class Base64PrintFileCommandSet(WshellCommandSet):
    """
    Overwrite `cat` (in Linux and Windows PSH) and `type` (in Windows CMD) to get file content
    as base64 to avoid some issues when manipulating the output (eg. escape \n)
    """

    @override
    def on_register(self, cmd: Cmd):
        super().on_register(cmd)

        if cmd.injector.is_windows_cmd():
            self.get_base64_encoded_file_func = self.windows_cmd_get_base64_encoded_file
            setattr(cmd, "do_type", self.get_file_content)
            cmd.hidden_commands.append("type")
        else:
            if cmd.injector.is_linux():
                self.get_base64_encoded_file_func = self.linux_get_base64_encoded_file
            elif cmd.injector.is_windows_psh():
                self.do_cat = self.windows_psh_get_base64_encoded_file

            setattr(cmd, "do_cat", self.get_file_content)
            cmd.hidden_commands.append("cat")


    def get_file_content(self, filename: str):
        base64_output = self.get_base64_encoded_file_func(filename)
        cmd: Cmd = self._cmd
        try:
            cmd.poutput(utils.base64_decode(base64_output))
        except BinasciiError:
            cmd.perror(base64_output)

    def get_base64_encoded_file_func(self, filename: str) -> str:
        """
        Abstract method to get the content of a file as a base64 encoded string

        Different operating systems require different commands to achieve this.
        The actual implementation is assigned during command set registration

        :param filename: the file to get the content from
        :return: the content of the file as a base64 encoded string
        """
        raise NotImplementedError

    def linux_get_base64_encoded_file(self, filename: str) -> str:
        return self._cmd.injector.execute(f"base64 '{filename}' 2>&1")

    def windows_psh_get_base64_encoded_file(self, filename: str) -> str:
        return self.execute(f"[System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content '{filename}')))")

    def windows_cmd_get_base64_encoded_file(self, filename: str) -> str:
        temp_filename = f"%TEMP%/{utils.random_string()}"
        return self.execute(
            f"certutil -encodehex -f '{filename}' {temp_filename} 0x40000001>nul&& \
            type {temp_filename} && \
            del {temp_filename}"
        )