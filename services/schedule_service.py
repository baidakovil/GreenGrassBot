from datetime import time
import logging
import services.logger

from telegram.ext import ConversationHandler

from commands.getevents import getEventsJob
from config import Cfg

logger = logging.getLogger('A.sch')
logger.setLevel(logging.DEBUG)

CFG = Cfg()

async def runsearch(update, context):
    """
    Result of the conversation: resheduling jobs.
    """
    logger.debug('Entered to runsearch()')
    userId = update.message.from_user.id
    chat_id = update.message.chat_id
    remove_job_if_exists(userId, context)
    logger.info(f'Job removed if any.')
    context.job_queue.run_daily(
                                callback=getEventsJob,
                                time=time.fromisoformat(CFG.DEFAULT_NOTICE_TIME),
                                chat_id=chat_id,
                                user_id=userId,
                                job_kwargs={'misfire_grace_time':3600*12,
                                            'coalesce':True}
                                )
    return ConversationHandler.END


def remove_job_if_exists(name: str, context) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


