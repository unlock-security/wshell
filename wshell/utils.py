"""
A collection of utility functions.
"""

from base64 import b64decode
from uuid import uuid4


def random_string() -> str:
    """ Returns a random string in UUID format (eg. 176e2d4b-1668-4292-bef8-48f0ebb670a0) """
    return str(uuid4())

def base64_decode(text: str) -> str:
    """ Decode base64-encoded text """
    return b64decode("".join(text.splitlines()), validate=True).decode(encoding='utf-8', errors='replace')