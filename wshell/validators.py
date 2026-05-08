""" A collection of validators to use in argument parsing """

import argparse
from collections.abc import Callable
from urllib.parse import urlparse

import requests.utils
from validator_collection import validators
from validator_collection.errors import InvalidURLError

from wshell.scripts import input_scripts, output_scripts


def http_url(value: str) -> str:
    """ Validate an HTTP(s) URL
    If no scheme is provided HTTP is used as default
    :param value: The value to validate
    :raise argparse.ArgumentTypeError if the value is not an URL or URL scheme is not HTTP nor HTTPS
    :return value if it is valid
    """
    url: str = requests.utils.prepend_scheme_if_needed(url=value, new_scheme="http")
    try:
        validators.url(
            url,
            allow_empty=False,
            allow_special_ips=True
        )
    except InvalidURLError as error:
        raise argparse.ArgumentTypeError(f"Invalid URL: {url}") from error
    else:
        scheme = urlparse(url).scheme
        if scheme not in ["http", "https"]:
            raise argparse.ArgumentTypeError(f"Invalid URL scheme: {scheme}")

    return url


def not_empty(value: str) -> str:
    """ Ensure the provided value is not None or empty
    :param value: The value to validate
    :raise argparse.ArgumentTypeError if the value is None or empty
    :return value if it is valid
    """
    if not value:
        raise argparse.ArgumentTypeError("Cannot use empty value")

    return value

def positive_integer(value: str) -> int:
    """ Ensure the provided value is a valid string representation of a positive integer number
    :param value: The value to validate
    :raise argparse.ArgumentTypeError if value is not integer or is <= 0
    :return value if it is valid
    """
    try:
        int_value = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Value must be numeric") from error

    if int_value <= 0:
        raise argparse.ArgumentTypeError("Value must be greater than zero")

    return int_value

def positive_float(value: str) -> float:
    """ Ensure the provided value is a valid string representation of a positive float number
    :param value: The value to validate
    :raise argparse.ArgumentTypeError if value is not float or is <= 0
    :return value if it is valid
    """
    try:
        float_value = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Value must be numeric") from error

    if float_value <= 0:
        raise argparse.ArgumentTypeError("Value must be greater than zero")

    return float_value

def timeout(value: str) -> Optional[float]:
    """ Ensure the provided value is a valid timeout value (non negative float number)
    :param value: The value to validate
    :raise argparse.ArgumentTypeError if value is not float or is < 0
    :return None if value is 0 or value if it is valid
    """
    try:
        float_value = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Value must be numeric") from error

    # Allow 0 to mean no timeout
    if float_value == 0:
        return None

    if float_value < 0:
        raise argparse.ArgumentTypeError("Value must be positive or zero")

    return float_value

def _scripts_chain(scripts_chain: str, valid_scripts: Dict[str, Callable[[str], str]]) -> List[Callable[[str], str]]:
    """ Validate a scripts chain
    :param scripts_chain: The comma-separated scripts chain to validate
    :param valid_scripts: A dictionary of valid scripts
    :raise argparse.ArgumentTypeError if the scripts chain is not valid
    :return A list of callable scripts based on scripts_chain
    """
    scripts_chain_list = scripts_chain.split(",")
    invalid_scripts = set(scripts_chain_list) - set(valid_scripts.keys())
    if invalid_scripts:
        raise argparse.ArgumentTypeError(f"Invalid scripts: {', '.join(invalid_scripts)}")

    return [valid_scripts[script] for script in scripts_chain_list]

def input_scripts_chain(scripts_chain: str) -> List[Callable[[str], str]]:
    """ Validate an input scripts chain
    :param scripts_chain: The comma-separated input scripts chain to validate
    :raise argparse.ArgumentTypeError if any of the input scripts chain element is not valid
    :return A list of callable input scripts based on scripts_chain
    """
    return _scripts_chain(scripts_chain, input_scripts)

def output_scripts_chain(scripts_chain: str) -> List[Callable[[str], str]]:
    """ Validate an output scripts chain
    :param scripts_chain: The comma-separated output scripts chain to validate
    :raise argparse.ArgumentTypeError if any of the output scripts chain element is not valid
    :return A list of callable output scripts based on scripts_chain
    """
    return _scripts_chain(scripts_chain, output_scripts)