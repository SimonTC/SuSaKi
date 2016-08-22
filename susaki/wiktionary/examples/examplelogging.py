import logging
from logging.handlers import TimedRotatingFileHandler
import os
from susaki.definitions import CRASH_DIR, QUERY_DIR


def query_filter(msg):
    return "Collecting article for" in msg.getMessage()


def setup_logging(debugging=False):

    os.makedirs(CRASH_DIR, exist_ok=True)
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(CRASH_DIR, 'crash'), when='s', interval=1, delay=True)
    error_handler.setLevel(logging.ERROR)

    os.makedirs(QUERY_DIR, exist_ok=True)
    querry_handler = TimedRotatingFileHandler(
        filename=os.path.join(QUERY_DIR, 'queries'), when='midnight')
    querry_handler.setLevel(logging.INFO)

    querry_handler.addFilter(query_filter)
    querry_handler.setFormatter(logging.Formatter("%(asctime)s: %(filename)s: %(message)s"))

    logger = logging.getLogger()
    logger.addHandler(error_handler)
    logger.addHandler(querry_handler)
    if debugging:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter("%(levelname)s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"))
        logger.addHandler(console_handler)
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger
