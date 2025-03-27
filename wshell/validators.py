""" A collection of validators to use in argument parsing """

import argparse
from urllib.parse import urlparse

import requests.utils
from validator_collection import validators
from validator_collection.errors import InvalidURLError


def http_url(value: str) -> str:
    """ Validate an HTTP(s) URL
    If no scheme is provided HTTP is used as default
    :param value: The value to validate
    :raise argparse.ArgumentTypeError if the value is not an URL or URL scheme is not HTTP nor HTTPS
    :return value if it is valid
    """
    url = requests.utils.prepend_scheme_if_needed(url=value, new_scheme="http")
    try:
        validators.url(
            url,
            allow_empty=False,
            allow_special_ips=True
        )
    except InvalidURLError:
        raise argparse.ArgumentTypeError(f"Invalid URL: {url}")
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


def positive_float(value: str) -> float:
    """ Ensure the provided value is a positive float number
    :param value: The value to validate
    :raise argparse.ArgumentTypeError if value is not float or is <= 0
    :return value if it is valid
    """
    try:
        value = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Value must be numeric")

    if value <= 0:
        raise argparse.ArgumentTypeError("Value must be greater than zero")

    return value
