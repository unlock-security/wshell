"""
A central registry for wshell commands to prevent conflicts and manage categories.
"""

from typing import Dict, List, Type

from cmd2 import categorize

from wshell.errors import CommandConflictError


class CommandRegistry:
    """
    A registry that discovers, validates, and stores command sets.
    It prevents command name collisions and manages command categories.
    """
    def __init__(self):
        self._commands: Dict[str, str] = {}  # { 'command_name': 'OwningClassName' }
        self._command_sets: List[Type] = []

    def register(self, command_set_cls: Type, category_name: str) -> None:
        """
        Inspects a command set class and registers it, checking for conflicts.

        :param command_set_cls: The WShellCommandSet class to register.
        :raises CommandConflictError: If a command is already registered by another class.
        """
        command_methods = [
            m for m in dir(command_set_cls) if m.startswith('do_') and callable(getattr(command_set_cls, m))
        ]

        for method_name in command_methods:
            command_name = method_name[3:]
            if command_name in self._commands:
                raise CommandConflictError(
                    f"Command '{command_name}' is already implemented by "
                    f"{self._commands[command_name]}. Cannot be re-registered by {command_set_cls.__name__}."
                )
            categorize(getattr(command_set_cls, method_name), category_name)
            self._commands[command_name] = command_set_cls.__name__

        self._command_sets.append(command_set_cls)

    def get_command_sets(self) -> List[Type]:
        """Returns the list of all validated and registered command set classes."""
        return self._command_sets


command_registry = CommandRegistry()
