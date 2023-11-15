import logging

from telegram import ReplyKeyboardRemove

from ui.news_builders import getInfoText
from db.db import Db
import services.logger

db = Db()

logger = logging.getLogger('A.get')
logger.setLevel(logging.DEBUG)

async def getEvents(update, context):
    userId = update.message.from_user.id
    infoText = await getInfoText(userId, db)
    if infoText:
        await update.message.reply_text(infoText, reply_markup=ReplyKeyboardRemove(),parse_mode='MarkdownV2')
        logger.info(f'infoText was sent to user {userId}')
    else:
        logger.info(f'I got empty infotext. Nothing to send to {userId}')


async def getEventsJob(context):
    """
    Sent list of artists with new concerts to user.
    Refresh sentEvents on disk to escape multiple user notification of similar events.
    Refresh lastEvents on disk (need for using /** command)
    """ 
    logger.info('Start getEventsJob')
    job = context.job
    userId = str(job.user_id)
    infoText = await getInfoText(userId, db)
    if infoText:
        await context.bot.send_message(
                                chat_id=job.chat_id,
                                text=infoText,
                                parse_mode='MarkdownV2')
        logger.info(f'Job done, infoText sent to user {userId}')
    else:
        logger.info(f'I got empty infotext. Nothing to send to {userId}')