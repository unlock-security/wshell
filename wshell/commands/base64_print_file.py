from binascii import Error as BinasciiError
from typing import override

from cmd2 import Cmd, CommandSet

from wshell import utils


class Base64PrintFileCommandSet(CommandSet):
    """
    Overwrite `cat` (in Linux and Windows PSH) and `type` (in Windows CMD) to get file content
    as base64 to avoid some issues when manipulating the output (eg. escape \n)
    """

    @override
    def on_register(self, cmd):
        super().on_register(cmd)

        if cmd.injector.is_windows_cmd():
            self.get_base64_encoded_file_func = self.windows_cmd_get_base64_encoded_file
            cmd.do_type = self.get_file_content
            cmd.hidden_commands.append("type")
        else:
            if cmd.injector.is_linux():
                self.get_base64_encoded_file_func = self.linux_get_base64_encoded_file
            elif cmd.injector.is_windows_psh():
                self.do_cat = self.windows_psh_get_base64_encoded_file

            cmd.do_cat = self.get_file_content
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
        return self._cmd.injector.execute(f"base64 \"{filename}\" 2>&1")

    def windows_psh_get_base64_encoded_file(self, filename: str) -> str:
        return self.execute(
            f"$file_content = Get-Content '{filename}'; [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($file_content))"
        )

    def windows_cmd_get_base64_encoded_file(self, filename: str) -> str:
        random_filename = utils.random_string()
        self.execute(f"certutil -encode '{filename}' %TEMP%/{random_filename}")
        base64_output = self.execute(f"type %TEMP%/{random_filename}")
        self.execute(f"del %TEMP%/{random_filename}")

        # `certutil` output will be something like:
        #
        # -----BEGIN CERTIFICATE-----
        # V1NoZWxsIGxldHMgeW91IHR1cm4gYSB3ZWItYmFzZWQge2NvZGUsY29tbWFuZCx0ZW1wbGF0ZX0g
        # aW5qZWN0aW9uIGluIGEgZnVsbCBmZWF0dXJlZCBzaGVsbCB3aXRoIGVhc2UuCg==
        # -----END CERTIFICATE-----
        #
        # So, we need to remove the first and the last lines
        #
        return base64_output[1:-2]