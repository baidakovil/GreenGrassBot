import os
from dotenv import load_dotenv
from ggbot import loadInteractions
from telegram.ext import Application, PicklePersistence


load_dotenv('.env')


def main():
    """
    Produce program launch. Shu!
    """
    logger.info(f'App started')
    token = os.getenv("BOT_TOKEN")
    persistence = PicklePersistence(filepath='connectBot')
    application = Application.builder().token(
        token).persistence(persistence).build()
    loadInteractions(application)
    application.run_polling()
    logger.info(f'Polling started')


if __name__ == '__main__':
    main()
