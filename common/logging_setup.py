"""
Hardening pass - structured logging.

print() statements have no timestamp, no severity level, and can't
be filtered or redirected to a file for later debugging. This gives
every module a real logger: timestamped, leveled (INFO/WARNING/
ERROR), and consistent across the whole project.
"""
import logging
import sys


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:  # avoid duplicate handlers if called twice
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
