import importlib
import inspect
import pkgutil
from typing import Iterable

from cmd2 import CommandSet


def load_command_sets() -> Iterable[CommandSet]:
    """Load all custom command sets in the modules from the commands package

    :return: a list of all of the command sets subclasses
    """
    for module_info in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{__package__}.{module_info.name}")
        for _, klass in inspect.getmembers(module, inspect.isclass):
            if issubclass(klass, CommandSet):
                yield klass
