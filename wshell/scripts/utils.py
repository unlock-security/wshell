import importlib
import pkgutil
from typing import Callable, Dict


def load_scripts(package: str, path: str) -> Dict[str, Callable[[str], str]]:
    """
    Load all Python modules in the given package and subpath,
    and return a dictionary of all functions with the correct signature and docstring.

    The correct signature is a single string argument, and returning a string.

    :param package: The name of the package to load scripts from
    :param path: The path to the package
    :return: A dictionary of all valid scripts
    """
    scripts = dict()

    for module_info in pkgutil.iter_modules(path):
        module = importlib.import_module(f"{package}.{module_info.name}")

        if hasattr(module, 'run') and callable(module.run):
            func = module.run

            # Check if the run function has the correct signature and provides a docstring
            # Valid function signature is: run(str) -> str
            if func.__code__.co_argcount == 1 \
                and all(arg_type is str for arg_type in func.__annotations__.values()) \
                and func.__doc__ is not None:
                    scripts[module_info.name] = func

    return scripts
