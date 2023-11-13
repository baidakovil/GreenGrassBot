import os
import logging
import logger
from dotenv import load_dotenv
from telegram.ext import Application, PicklePersistence

from ggbot import loadInteractions

load_dotenv('.env')

logger = logging.getLogger('A.A')
logger.setLevel(logging.DEBUG)

def main():
    """
    Produce program launch. Shu!
    """
    token = os.getenv("BOT_TOKEN")
    persistence = PicklePersistence(filepath='connectBot')
    application = Application.builder().token(
        token).persistence(persistence).build()
    loadInteractions(application)
    logger.info(f'App started')
    application.run_polling()

if __name__ == '__main__':
    main()