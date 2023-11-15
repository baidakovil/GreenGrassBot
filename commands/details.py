import logging

from telegram import Update
from telegram.ext import CallbackContext

from db.db import Db
from services.message_service import reply
from ui.news_builders import getNewsText


db = Db()

logger = logging.getLogger('A.det')
logger.setLevel(logging.DEBUG)

async def details(update: Update, context: CallbackContext) -> None:
    """
    Sends detailed info about events of the artist, chosen by user with command /xx.
    xx in /xx called shorthand.
    """
    user_id = str(update.message.from_user.id)
    command = update.message.text
    shorthand = int(command[1:])
    text = await getNewsText(user_id, shorthand, db)
    await reply(update, text, disable_web_page_preview=True)
    
    logger.info(f'Details was sent to {user_id}')
    return None