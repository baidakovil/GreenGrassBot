import logging
from datetime import datetime

from telegram import ReplyKeyboardRemove

from config import Cfg

logger = logging.getLogger('A.uti')
logger.setLevel(logging.DEBUG)

CFG = Cfg()

def timestamp_to_text(timestamp):
    f = '%Y-%m-%d %H:%M:%S'
    return timestamp.strftime(f)

def date_to_text(date):
    f = '%Y-%m-%d'
    return date.strftime(f)

def text_to_userdate(text):
    """
    Uses to convert date from DB-storing format '2023-01-02' to '02 Jan 2023' for humans. 
    """
    f_text = '%Y-%m-%d'
    f_user = '%d %b %Y'
    return datetime.strptime(text, f_text).strftime(f_user)

async def cancel_handle(update, context):
    """
    Determine what to do when update causes error.
    """
    user = update.message.from_user
    logger.info(f'User {user.first_name} canceled the conversation')
    await update.message.reply_text(
        text='Canceled',
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END

