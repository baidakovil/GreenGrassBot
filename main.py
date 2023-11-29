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
