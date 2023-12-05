# Green Grass Bot — A program to notify about concerts of artists you listened to.
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
from dotenv import load_dotenv

load_dotenv('.env')
from telegram.ext import Application

from config import Cfg
from db.db import Db
from interactions.loader import load_interactions
from services.logger import logger
from services.schedule_service import reschedule_jobs

CFG = Cfg()
i18n.load_path.append(CFG.PATH_TRANSLATIONS)
i18n.set('filename_format', CFG.FILENAME_FORMAT_I18N)
i18n.set('locale', CFG.DEFAULT_LOCALE)

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
        .read_timeout(CFG.SEC_READ_TIMEOUT)
        .write_timeout(CFG.SEC_WRITE_TIMEOUT)
        .concurrent_updates(True)
        .build()
    )
    load_interactions(application)
    reschedule_jobs(application, db)
    logger.info(f'App started')
    application.run_polling()
    return None


if __name__ == '__main__':
    main()
