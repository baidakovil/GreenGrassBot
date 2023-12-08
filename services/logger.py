# Green Grass Bot — Ties the music you're listening to with the concert it's playing at.
# Copyright (C) 2021-2023 Ilia Baidakov <baidakovil@gmail.com>

# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <https://www.gnu.org/licenses/>.
"""This file contains logger logic."""

import logging
import os
from logging import Logger
from logging.handlers import RotatingFileHandler

import config as cfg


def start_logger() -> Logger:
    """
    Loggers definition. Logger in logger.py is the highest (A), other are descendants:
    A.uti, A.db, etc.
    """
    gen_logger = logging.getLogger('A')
    gen_logger.setLevel(logging.DEBUG)
    gen_logger.propagate = False

    #  Logging to console.
    ch = logging.StreamHandler()
    os.makedirs(cfg.PATH_LOGGER, exist_ok=True)
    #  Logging to file, continuous after bot restart.
    rh = RotatingFileHandler(
        filename=os.path.join(cfg.PATH_LOGGER, cfg.FILE_ROTATING_LOGGER),
        mode='a',
        maxBytes=cfg.BYTES_MAX_ROTATING_LOGGER,
        backupCount=cfg.QTY_BACKUPS_ROTATING_LOGGER,
    )
    ch_formatter = logging.Formatter(
        '[%(asctime)s.%(msecs)03d - %(name)5s - %(levelname)8s:%(lineno)3d - \
        %(funcName)18s()] %(message)s',
        '%H:%M:%S',
    )
    rh_formatter = logging.Formatter(
        '[%(asctime)s.%(msecs)03d - %(name)5s - %(levelname)8s:%(lineno)3d - \
        %(funcName)18s() - %(filename)8s - %(threadName)10s] %(message)s',
        '%Y-%m-%d %H:%M:%S',
    )
    ch.setLevel(logging.DEBUG)
    rh.setLevel(logging.DEBUG)
    ch.setFormatter(ch_formatter)
    rh.setFormatter(rh_formatter)
    gen_logger.addHandler(ch)
    gen_logger.addHandler(rh)
    return gen_logger


logger = start_logger()
logger.info('Main logger started, __name__ is %s', __name__)
