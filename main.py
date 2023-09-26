import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from ggbot import loadInteractions
from telegram.ext import Application, PicklePersistence

BOT_FOLDER = os.path.dirname(os.path.realpath(__file__))


def startLogger():
    """
    Loggers definition. 
    Logger in main.py is highest logger (A), other are descendants (A.B, A.C)
    """
    logger = logging.getLogger('A')
    logger.setLevel(logging.DEBUG)

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
        filename=os.path.join(BOT_FOLDER, 'logger.log'),
        mode='w')
    #  Logging to file, continuous after bot restart.
    rh = RotatingFileHandler(
        filename=os.path.join(BOT_FOLDER, 'data/log/logger_rotating.log'),
        mode='a',
        maxBytes=1024*1024*20,
        backupCount=5)
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
    ch_filter = ContextFilter()
    ch.addFilter(ch_filter)
    return logger


logger = startLogger()
logger.info(f'App started, __name__ is {__name__}')

dotenv_path = os.path.join(BOT_FOLDER, '.env')
load_dotenv(dotenv_path)


def main():
    """
    Produce program launch. Shu!
    """
    token = os.getenv("BOT_TOKEN")
    persistence = PicklePersistence(filepath='connectBot')
    application = Application.builder().token(
        token).persistence(persistence).build()
    loadInteractions(application)
    application.run_polling()
    logger.info(f'Polling started')


if __name__ == '__main__':
    main()
