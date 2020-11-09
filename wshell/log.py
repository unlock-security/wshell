import logging
import sys


logger = logging.getLogger("wshell")

logger_handler = logging.StreamHandler(sys.stderr)
logger_formatter = logging.Formatter(fmt="[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger_handler.setFormatter(logger_formatter)

logger.addHandler(logger_handler)
