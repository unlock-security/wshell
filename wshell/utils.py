"""
A collection of utility functions.
"""

from uuid import uuid4


def random_string() -> str:
    """ Returns a random string in UUID format (eg. 176e2d4b-1668-4292-bef8-48f0ebb670a0) """
    return str(uuid4())
