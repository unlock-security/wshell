import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any

from cmd2 import Cmd, CommandSet

from wshell.commands.registry import command_registry
from wshell.errors import UnsupportedFeatureError, WrongCommandSetTypeError


class WShellCommandSet(CommandSet):
    """Base class for wshell command sets"""

    def _dispatch(self, func_name: str, *args, **kwargs) -> Any:
        """
        Dispatches the call to the correct OS-specific implementation of a feature.

        This method dynamically calls an OS-specific function based on the detected
        target operating system. Implementations for a given feature must follow
        the naming convention: `_{os_name}_{func_name}`.

        The `os_name` part is derived from `wshell.injector.OSEnum`
        (e.g., 'linux', 'win-cmd', 'win-psh').

        Args:
            func_name (str): The base name of the feature to dispatch
            *args: Positional arguments to pass to the OS-specific implementation.
            **kwargs: Keyword arguments to pass to the OS-specific implementation.

        Returns:
            Any: The result returned by the OS-specific implementation.

        Raises:
            UnsupportedFeatureError: If no OS-specific implementation is found
                                     for the current target OS and the given `func_name`.

        Example:
            If `func_name` is "get_file_size" and the target OS is Linux, this method
            will attempt to call `self._linux_get_file_size(*args, **kwargs)`.
        """
        os_name = self._cmd.injector.OS.value.replace('-', '_')  # linux, win_cmd, win_psh
        method_name = f"_{os_name}_{func_name}"
        method = getattr(self, method_name, None)

        if not callable(method):
            raise UnsupportedFeatureError(f"Feature '{func_name}' is not supported on {self._cmd.injector.OS.value}")

        return method(*args, **kwargs)

    def on_register(self, cmd: Cmd) -> None:
        # Avoid circular dependencies with cmd component
        from wshell.cmd import WShellCmd

        if not isinstance(cmd, WShellCmd):
            raise WrongCommandSetTypeError(f"Expected {WShellCmd.__name__}, got {type(cmd).__name__}")

        super().on_register(cmd)


def load_commands() -> None:
    """
    Discover and load all command sets from the commands directory.
    Categories are determined by the subdirectory name.
    """
    commands_path = Path(__path__[0])
    for category_dir in commands_path.iterdir():
        if category_dir.is_dir():
            category_name = " ".join(word for word in category_dir.name.split("_")).capitalize()

            for module_info in pkgutil.iter_modules([str(category_dir)]):
                module = importlib.import_module(f"{__package__}.{category_dir.name}.{module_info.name}")
                for _, cls in inspect.getmembers(module, inspect.isclass):
                    if issubclass(cls, WShellCommandSet) and cls is not WShellCommandSet:
                        command_registry.register(cls, category_name)
