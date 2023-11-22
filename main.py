import logging
import os

import i18n
from dotenv import load_dotenv
from telegram.ext import Application

from db.db import Db
from interactions.loader import load_interactions
from services.logger import logger
from services.schedule_service import reschedule_jobs

load_dotenv('.env')
i18n.load_path.append('./assets/lang')
i18n.set('filename_format', '{locale}.{format}')
i18n.set('locale', os.getenv("LANGUAGE"))

logger = logging.getLogger('A.A')
logger.setLevel(logging.DEBUG)


def main() -> None:
    """
    Produce program launch. Shu!
    """
    token = os.environ['BOT_TOKEN']
    db = Db(initial=True)
    application = Application.builder().token(token).build()
    load_interactions(application)
    reschedule_jobs(application, db)
    logger.info(f'App started')
    application.run_polling()
    return None


if __name__ == '__main__':
    main()
