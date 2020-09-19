""" A collection of validators to use in argument parsing """

import argparse
from validator_collection import validators
from validator_collection.errors import InvalidURLError
from urllib.parse import urlparse


def http_url(value: str) -> str:
    """ Validate an HTTP(s) URL
    :param value: The value to validate
    :raise argparse.ArgumentTypeError if the value is not an URL or URL scheme is not HTTP nor HTTPS
    :return value if it is valid
    """
    try:
        validators.url(
            value,
            allow_empty=False,
            allow_special_ips=True
        )
    except InvalidURLError:
        raise argparse.ArgumentTypeError(f"Invalid URL: {value}")
    else:
        scheme = urlparse(value).scheme
        if scheme not in ["http", "https"]:
            raise argparse.ArgumentTypeError(f"Invalid URL scheme: {scheme}")

    return value


def not_empty(value: str) -> str:
    """ Validate an HTTP(s) URL
    :param value: The value to validate
    :raise argparse.ArgumentTypeError if the value is None or empty
    :return value if it is valid
    """
    if not value:
        raise argparse.ArgumentTypeError(f"Cannot use empty value")

    return value
