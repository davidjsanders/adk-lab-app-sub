import logging

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


def setup_logging(level=logging.INFO):
    """Configures root logger with the standard formatter and level.

    Args:
        level: Minimum logging level (e.g. logging.INFO or logging.DEBUG).
    """
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        force=True
    )
