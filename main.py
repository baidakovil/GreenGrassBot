import os
import logging
from dotenv import load_dotenv
import i18n
from telegram.ext import Application, PicklePersistence

from db.db import Db
from interactions.loader import load_interactions

load_dotenv('.env')
i18n.load_path.append('./assets/lang')
i18n.set('filename_format', '{locale}.{format}')
i18n.set('locale', os.getenv("LANGUAGE"))

logger = logging.getLogger('A.A')
logger.setLevel(logging.DEBUG)

def main():
    """
    Produce program launch. Shu!
    """
    token = os.getenv("BOT_TOKEN")  
    persistence = PicklePersistence(filepath='connectBot')
    Db(initial=True)
    application = Application.builder().token(
        token).persistence(persistence).build()
    load_interactions(application)
    logger.info(f'App started')
    application.run_polling()

if __name__ == '__main__':
    main()