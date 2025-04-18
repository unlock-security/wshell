from wshell.status import ExitStatus


class WShellError(Exception):
    """ The base wshell error class """
    EXIT_STATUS = ExitStatus.GENERIC_ERROR


class InjectorError(WShellError):
    """ The base class for injectors-related errors """


class CommandExecutionError(InjectorError):
    """ The command execution failed """
    EXIT_STATUS = ExitStatus.ERROR_CANNOT_EXECUTE


class OsDetectionError(InjectorError):
    """ The automatic OS detection failed """
    EXIT_STATUS = ExitStatus.ERROR_UNDETECTED_OS


class HttpError(WShellError):
    """ The base class for http-related errors """


class TargetUnreachableError(HttpError):
    """ The target is unreachable, cannot connect """
    EXIT_STATUS = ExitStatus.ERROR_TARGET_UNREACHABLE


class TimeoutExpiredError(HttpError):
    """ The timeout for connect/read/write is expired """
    EXIT_STATUS = ExitStatus.ERROR_TIMEOUT_EXPIRED

class UnsupportedFeatureError(WShellError):
    """ The feature is not supported for the current OS """
    EXIT_STATUS = ExitStatus.ERROR_UNSUPPORTED_FEATURE