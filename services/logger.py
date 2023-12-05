#  Green Grass Bot — A program to notify about concerts of artists you listened to.
#  Copyright (C) 2021-2023 Ilia Baidakov <baidakovil@gmail.com>
#  This program is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software Foundation:
#  GPLv3 or any later version at your option. License: <https://www.gnu.org/licenses/>.
"""This file contains logger logic."""

import logging
import os
from logging import Logger
from logging.handlers import RotatingFileHandler

from config import Cfg

CFG = Cfg()


def start_logger() -> Logger:
    """
    Loggers definition. Logger in logger.py is the highest (A), other are descendants:
    A.uti, A.db, etc.
    """
    logger = logging.getLogger('A')
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    #  Logging to console.
    ch = logging.StreamHandler()
    os.makedirs(CFG.PATH_LOGGER, exist_ok=True)
    #  Logging to file, continuous after bot restart.
    rh = RotatingFileHandler(
        filename=os.path.join(CFG.PATH_LOGGER, CFG.FILE_ROTATING_LOGGER),
        mode='a',
        maxBytes=CFG.BYTES_MAX_ROTATING_LOGGER,
        backupCount=CFG.QTY_BACKUPS_ROTATING_LOGGER,
    )
    ch_formatter = logging.Formatter(
        '[%(asctime)s.%(msecs)03d - %(name)5s - %(levelname)8s:%(lineno)3d - %(funcName)18s()] %(message)s',
        '%H:%M:%S',
    )
    rh_formatter = logging.Formatter(
        '[%(asctime)s.%(msecs)03d - %(name)5s - %(levelname)8s:%(lineno)3d - %(funcName)18s() - %(filename)8s - %(threadName)10s] %(message)s',
        '%Y-%m-%d %H:%M:%S',
    )
    ch.setLevel(logging.INFO)
    rh.setLevel(logging.DEBUG)
    ch.setFormatter(ch_formatter)
    rh.setFormatter(rh_formatter)
    logger.addHandler(ch)
    logger.addHandler(rh)
    return logger


logger = start_logger()
logger.info(f'Main logger started, __name__ is {__name__}')
