# Green Grass Bot — Ties the music you're listening to with the concert it's playing at.
# Copyright (C) 2021-2023 Ilia Baidakov <baidakovil@gmail.com>

# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <https://www.gnu.org/licenses/>.
"""This file, like other in /commands, contains callback funcs for same name command."""

import asyncio
import logging

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import CallbackContext, Job

import config as cfg
from db.db_service import Db
from services.custom_classes import UserSettings
from services.logger import logger
from services.message_service import i34g, reply, send_message, up_full
from ui.news_builders import prepare_gigs_text

db = Db()

logger = logging.getLogger('A.get')
logger.setLevel(logging.DEBUG)

sem_atrequest = asyncio.Semaphore(cfg.MAX_CONCURRENT_CONN_ATREQUEST)
sem_atjob = asyncio.Semaphore(cfg.MAX_CONCURRENT_CONN_ATJOB)


async def getgigs(update: Update, context: CallbackContext) -> None:
    """
    Callback function. Send list of artists with new concerts to user.
    Args:
        update, context: standart PTB callback signature
    TODO avoid concurrent last.fm requests with context.application.create_task():
    github.com/python-telegram-bot/python-telegram-bot/wiki/Concurrency
    TODO self-edited "please wait" message
    """
    user_id, chat_id, _, _ = up_full(update)
    usersettings = await db.rsql_settings(user_id)
    if (usersettings is None) or (not await db.rsql_lfmuser(user_id)):
        text = await i34g('getgigs.error', user_id=user_id)
        await reply(update, text)
        return None

    assert isinstance(usersettings, UserSettings)

    please_wait_text = await i34g('getgigs.pleasewait', user_id=user_id)
    please_wait_msg = await send_message(context, chat_id, please_wait_text)

    async with sem_atrequest:
        logger.info('Start getgigs() for user_id %s', user_id)
        text = await prepare_gigs_text(user_id, request=True)

    await context.bot.deleteMessage(
        message_id=please_wait_msg.message_id, chat_id=chat_id
    )
    if text:
        await reply(update, text, reply_markup=ReplyKeyboardRemove())
        logger.info('Gigs sent to user %s', user_id)
        return None
    logger.warning('Got empty gigs_text on request. Smth wrong with %s', user_id)
    return None


async def getgigs_job(context: CallbackContext) -> None:
    """
    Callback function for job scheduler. Send list of artists with new concerts to user.
    Args:
        context: context object generated by telegram.ext.Application
        when user adds lastfm useracc
    """
    if isinstance(context.job, Job):
        user_id = context.job.user_id
        chat_id = context.job.chat_id
        if user_id is None or chat_id is None:
            logger.warning('CONTEXT DOES NOT CONTAIN user_id or chat_id')
            return None
    else:
        logger.warning('CONTEXT DOES NOT CONTAIN JOB')
        return None
    assert user_id
    assert chat_id

    async with sem_atjob:
        logger.info('Start getgigs_job() for user_id %s', user_id)
        text = await prepare_gigs_text(user_id, request=False)
    if text:
        await send_message(context, chat_id, text)
        logger.info('Job done, gigs sent to user %s', user_id)
        return None
    else:
        logger.info('Got empty gigs text. Nothing to send to %s', user_id)
        return None
