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
"""This is main execution program file."""

import logging
import os

import i18n
from telegram import Update
from telegram.ext import Application

import config as cfg
from db.db_service import Db
from interactions.loader import load_interactions
from services.logger import logger
from services.schedule_service import reschedule_jobs
from ui.commands_setter import set_commands
from ui.descriptions_setter import set_descriptions

i18n.load_path.append(cfg.PATH_TRANSLATIONS)
i18n.set('filename_format', cfg.FILENAME_FORMAT_I18N)
i18n.set('locale', cfg.LOCALE_DEFAULT)

logger = logging.getLogger('A.A')
logger.setLevel(logging.DEBUG)


def main() -> None:
    """
    Produce program launch. Shu!
    """
    token = os.environ['BOT_TOKEN']
    db = Db(initial=True)
    application = (
        Application.builder()
        .token(token)
        .read_timeout(cfg.SEC_READ_TIMEOUT)
        .write_timeout(cfg.SEC_WRITE_TIMEOUT)
        .build()
    )
    load_interactions(application)
    reschedule_jobs(application, db)
    set_descriptions(application)
    set_commands(application)
    logger.info('App started')
    application.run_polling(allowed_updates=[Update.MESSAGE])


if __name__ == '__main__':
    main()
