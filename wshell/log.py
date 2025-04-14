import sys

import colorlog

logger = colorlog.getLogger("wshell")

_logger_handler = colorlog.StreamHandler(sys.stderr)
_logger_handler.setFormatter(
    colorlog.ColoredFormatter(
        fmt="[%(thin_cyan)s%(asctime)s%(reset)s] [%(log_color)s%(levelname)s%(reset)s] %(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG':    'purple',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        }
    )
)
logger.addHandler(_logger_handler)
