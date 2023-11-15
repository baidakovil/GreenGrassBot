import logging

from telegram import ReplyKeyboardRemove
from telegram import Update
from telegram.ext import CallbackContext

from ui.news_builders import prepare_gigs_text
from services.message_service import reply
from db.db import Db

db = Db()

logger = logging.getLogger('A.get')
logger.setLevel(logging.DEBUG)

async def get_gigs(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = await prepare_gigs_text(user_id, db)
    if text:
        await reply(update, text, reply_markup=ReplyKeyboardRemove())
        logger.info(f'Gigs sent to user {user_id}')
        return None
    else:
        logger.info(f'Got empty gigs text. Nothing to send to {user_id}')
        return None


async def get_gigs_job(context) -> None:
    """
    Sent list of artists with new concerts to user.
    Refresh sentEvents on disk to escape multiple user notification of similar events.
    Refresh lastEvents on disk (need for using /** command)
    """ 
    logger.info('Start getEventsJob')
    user_id = context.job.user_id
    text = await prepare_gigs_text(user_id, db)
    if text:
        await context.bot.send_message(
                                chat_id=context.job.chat_id,
                                text=text,
                                parse_mode='MarkdownV2')
        logger.info(f'Job done, gigs sent to user {user_id}')
        return None
    else:
        logger.info(f'Got empty gigs text. Nothing to send to {user_id}')
        return None