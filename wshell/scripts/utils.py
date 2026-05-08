import importlib
import inspect
import pkgutil
from collections.abc import MutableSequence
from typing import Protocol, TypeGuard, get_type_hints

from wshell.log import logger


class Script(Protocol):
    """Protocol implemented by input/output scripts."""

    def __call__(self, text: str) -> str: ...


def load_scripts(package: str, path: MutableSequence[str]) -> dict[str, Script]:
    """
    Load all Python modules in the given package and subpath,
    and return a dictionary of all functions with the correct signature and docstring.

    The correct signature is a single string argument, and returning a string.

    :param package: The name of the package to load scripts from
    :param path: The path to the package
    :return: A dictionary of all valid scripts
    """
    scripts: dict[str, Script] = {}

    for module_info in pkgutil.iter_modules(path):
        module = importlib.import_module(f"{package}.{module_info.name}")

        func = getattr(module, "run", None)
        if _is_valid_script(func):
            scripts[module_info.name] = func
            continue

        logger.warning(f"'{package}.{module_info.name}' is not valid a script. Skipping...")

    return scripts


def _is_valid_script(func: object) -> TypeGuard[Script]:
    """Validate that a script exposes `run(text: str) -> str` with a docstring."""
    if not callable(func):
        return False

    if not func.__doc__ or not func.__doc__.strip():
        return False

    signature = inspect.signature(func)
    if len(signature.parameters) != 1:
        return False

    parameter = next(iter(signature.parameters.values()))
    hints = get_type_hints(func)
    return hints.get(parameter.name) is str and hints.get("return") is str
