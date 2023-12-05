#  Green Grass Bot — A program to notify about concerts of artists you listened to.
#  Copyright (C) 2021-2023 Ilia Baidakov <baidakovil@gmail.com>
#  This program is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software Foundation:
#  GPLv3 or any later version at your option. License: <https://www.gnu.org/licenses/>.
"""This file contains logic for continuous user notification about new concerts."""

import logging
from datetime import time
from typing import Union

from telegram import Update
from telegram.ext import Application, CallbackContext, ConversationHandler, JobQueue

from commands.getgigs import getgigs_job
from config import Cfg
from db.db import Db
from services.logger import logger
from services.message_service import up_full

logger = logging.getLogger('A.sch')
logger.setLevel(logging.DEBUG)

CFG = Cfg()

db = Db()


def get_job_name(user_id: int, chat_id: int) -> str:
    """
    Provide convenient (inside bot) name for job. It included chat_id to make it
    possible to have bot in chats. At least, in future.
    Args:
        user_id: Tg field user_id
        chat_id: Tf field chat_id
    """
    return str(user_id) + '_' + str(chat_id)


def run_daily_job(
    user_id: int, chat_id: int, job_src: Union[CallbackContext, Application]
) -> None:
    """
    Add job getgigs_job to scheduler.
    Args:
        user_id: Tg field user_id
        chat_id: Tf field chat_id
        job_src: object with "current_jobs" method to obtain current jobs
    """
    logger.debug(f'Entered to run_daily_job() for: {user_id}, {chat_id}')
    if isinstance(job_src.job_queue, JobQueue):
        job_src.job_queue.run_daily(
            callback=getgigs_job,
            time=time.fromisoformat(CFG.DEFAULT_NOTICE_TIME),
            chat_id=chat_id,
            user_id=user_id,
            name=get_job_name(user_id, chat_id),
            job_kwargs=CFG.CRON_JOB_KWARGS,
        )
    else:
        logger.warning('Can not access JobQueue. Something wrong')
    return None


async def add_daily(update: Update, context: CallbackContext) -> int:
    """
    Result of the "connect" conversation: job scheduling.
    Args:
        update, context: standart PTB callback signature
    Returns:
        signal for stop of conversation
    """
    logger.debug('Entered to add_daily()')
    user_id, chat_id, _, _ = up_full(update)

    remove_jobs(user_id, chat_id, context)
    run_daily_job(user_id, chat_id, context)
    await db.wsql_jobs(user_id, chat_id)

    logger.info(f'Added daily job for: {user_id}')
    return ConversationHandler.END


def remove_jobs(
    user_id: int, chat_id: int, job_src: Union[CallbackContext, Application]
) -> None:
    """
    Procedure to remove jobs. Runs when disconnect lastfm accounts or assign new jobs.
    Args:
        user_id: Tg field user_id
        chat_id: Tf field chat_id
        job_src: object with "current_jobs" method to obtain current jobs
    """
    job_name = get_job_name(user_id, chat_id)
    if isinstance(job_src.job_queue, JobQueue):
        current_jobs = job_src.job_queue.get_jobs_by_name(job_name)
        if current_jobs:
            count_jobs = 0
            for job in current_jobs:
                job.schedule_removal()
                count_jobs += 1
            logger.debug(f'Jobs removed: {count_jobs}')
    else:
        logger.warning('Can not access JobQueue. Something wrong')
    return None


def reschedule_jobs(application: Application, db) -> None:
    """
    Procedure to recover jobs when bot starts. Used as persistence tool.
    Args:
        application: object with "job_queue" method to obtain current jobs
    """
    logger.debug('Entered to reschedule_jobs()')
    jobs = db.rsql_jobs()
    for job in jobs:
        user_id, chat_id = job
        remove_jobs(user_id, chat_id, application)
        run_daily_job(user_id, chat_id, application)
        return None
