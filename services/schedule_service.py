import logging
from datetime import time

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from commands.getgigs import getgigs_job
from config import Cfg

logger = logging.getLogger('A.sch')
logger.setLevel(logging.DEBUG)

CFG = Cfg()


async def run_daily(update: Update, context: CallbackContext) -> int:
    """
    Result of the "connect" conversation: job resheduling.
    Args:
        update, context: standart PTB callback signature
    Returns:
        signal for stop of conversation
    """
    logger.debug('Entered to run_daily()')
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    current_jobs = context.job_queue.get_jobs_by_name(str(user_id))
    if current_jobs:
        count_jobs = 0
        for job in current_jobs:
            job.schedule_removal()
            count_jobs += 1
        logger.debug('Schedules removed: {count_jobs}')

    context.job_queue.run_daily(
        callback=getgigs_job,
        time=time.fromisoformat(CFG.DEFAULT_NOTICE_TIME),
        chat_id=chat_id,
        user_id=user_id,
        name=str(user_id),
        job_kwargs={'misfire_grace_time': 3600 * 12, 'coalesce': True},
    )
    logger.info('Added daily job for: {user_id}')
    return ConversationHandler.END
