import colorlog
import sys

logger = colorlog.getLogger("wshell")

logger_handler = colorlog.StreamHandler(sys.stderr)
logger_handler.setFormatter(
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
logger.addHandler(logger_handler)
