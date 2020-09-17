from enum import IntEnum, unique


@unique
class ExitStatus(IntEnum):
    """ Program exit status code constants """
    SUCCESS = 0
    GENERIC_ERROR = 1

    ERROR_CTRL_C = 130
