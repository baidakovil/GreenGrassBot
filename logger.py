import os
import logging
from logging.handlers import RotatingFileHandler

from config import Cfg

CFG = Cfg()

def startLogger():
    """
    Loggers definition. 
    Logger in logger.py is highest logger (A), other are descendants (A.A, A.B, A.C)
    """
    logger = logging.getLogger('A')
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    class ContextFilter(logging.Filter):
        """
        Necessary to escape message dublications in console in
        case when logger.setLevel of A logger lower then A.B (debugging case)
        """

        def filter(self, record):
            if (record.name == 'A') and (record.levelname == 'DEBUG'):
                return 0
            else:
                return 1
    #  Logging to console.
    ch = logging.StreamHandler()
    #  Logging to file since last run (debugging case).
    fh = logging.FileHandler(
        filename=os.path.join(CFG.PATH_LOGGER, CFG.FILE_SESSION_LOGGER),
        mode='w')
    os.makedirs(CFG.PATH_LOGGER, exist_ok=True)
    #  Logging to file, continuous after bot restart.
    rh = RotatingFileHandler(
        filename=os.path.join(CFG.PATH_LOGGER, CFG.FILE_ROTATING_LOGGER),
        mode='a',
        maxBytes=CFG.BYTES_MAX_ROTATING_LOGGER,
        backupCount=CFG.QTY_BACKUPS_ROTATING_LOGGER)
    ch_formatter = logging.Formatter(
        '[%(asctime)s.%(msecs)03d - %(name)3s - %(levelname)8s - %(funcName)18s()] %(message)s',
        '%H:%M:%S')
    fh_formatter = logging.Formatter(
        '[%(asctime)s.%(msecs)03d - %(name)20s - %(filename)20s:%(lineno)4s - %(funcName)20s() - %(levelname)8s - %(threadName)10s] %(message)s',
        '%Y-%m-%d %H:%M:%S')
    ch.setLevel(logging.DEBUG)
    fh.setLevel(logging.DEBUG)
    rh.setLevel(logging.DEBUG)
    ch.setFormatter(ch_formatter)
    fh.setFormatter(fh_formatter)
    rh.setFormatter(fh_formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.addHandler(rh)
    # ch_filter = ContextFilter()
    # ch.addFilter(ch_filter)
    return logger

logger = startLogger()
logger.info(f'Main logger started, __name__ is {__name__}')
