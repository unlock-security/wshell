from enum import IntEnum, unique


@unique
class ExitStatus(IntEnum):
    """ Program exit status code constants """

    # Generic
    SUCCESS = 0
    GENERIC_ERROR = 1

    # Injectors
    ERROR_CANNOT_EXECUTE = 10
    ERROR_UNDETECTED_OS = 11

    # HTTP
    ERROR_TARGET_UNREACHABLE = 20
    ERROR_TIMEOUT_EXPIRED = 21

    # Command Sets
    ERROR_UNSUPPORTED_FEATURE = 30

    # Signals
    ERROR_CTRL_C = 130
