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
"""This file contains logic related to conversation started at /connect command."""

import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

import config as cfg
from db.db_service import Db
from interactions.common_handlers import cancel_handle
from services.logger import logger
from services.message_service import i34g, reply, up, up_full
from services.parse_services import check_valid_lfm
from services.schedule_service import add_daily

logger = logging.getLogger('A.con')
logger.setLevel(logging.DEBUG)

db = Db()


USERNAME = 0


async def connect(update: Update, _context: CallbackContext) -> Optional[int]:
    """
    Entry point. Asks the lastfm username. Stop conversation if max acc qty reached by
    user.
    Args:
        update, context: standart PTB callback signature
    Returns:
        signals for stop or next step of conversation
    """
    await db.save_user(update)
    user_id = up(update)
    useraccs = await db.rsql_lfmuser(user_id=user_id)
    if len(useraccs) >= cfg.MAX_LFM_ACCOUNT_QTY:
        await reply(
            update,
            await i34g(
                'conn_lfm_conversation.max_acc_reached',
                qty=cfg.MAX_LFM_ACCOUNT_QTY,
                user_id=user_id,
            ),
        )
        return ConversationHandler.END
    await reply(update, await i34g('conn_lfm_conversation.enter_lfm', user_id=user_id))
    return USERNAME


async def username(update: Update, context: CallbackContext) -> int:
    """
    Second step. Gets lastfm username and check it. Variants possible: a) Name already
    in db -> Message -> END b) Name give error -> Message -> END c) Ok in lastfm and
    added -> Message -> add_daily.
    Args:
        update, context: standart PTB callback signature
    Returns:
        signals for stop or next step of conversation

    #TODO Error when command after /connect Oups! We get error 500 when load tracks from
    Last.fm for /delete.
    """
    logger.debug('Entered to username()')
    user_id, _, acc, _ = up_full(update)
    acc = acc.lower()
    useraccs = await db.rsql_lfmuser(user_id)
    if acc in useraccs:
        await reply(
            update,
            await i34g('conn_lfm_conversation.already_have', acc=acc, user_id=user_id),
        )
        return ConversationHandler.END

    acc_valid, diagnosis = await check_valid_lfm(acc, user_id)
    if not acc_valid:
        await reply(update, diagnosis)
        logger.info(
            'User %s tried to added lfm account: %s, but acc is not valid',
            user_id,
            acc,
        )
        return ConversationHandler.END

    affected_rows = await db.wsql_useraccs(user_id, acc)
    if affected_rows == 1:
        text = await i34g('conn_lfm_conversation.done', acc=acc, user_id=user_id)
        if len(await db.rsql_lfmuser(user_id)) == 1:
            text += await i34g(
                'conn_lfm_conversation.alarm_info',
                time=cfg.DEFAULT_NOTICE_TIME[:5],
                user_id=user_id,
            )
        await add_daily(update, context)
        await reply(update, text)
        logger.info('BotUser: %s have added lfm account:  %s', user_id, acc)
    else:
        await reply(
            update, await i34g('conn_lfm_conversation.some_error', user_id=user_id)
        )
        logger.info(
            'BotUser: %s tried to add lfm acc: %s but ended with error', user_id, acc
        )
    return ConversationHandler.END


def conn_lfm_conversation() -> ConversationHandler:
    """
    Function-placeholder for returning conversation handler to add lastfm user.
    Returns:
        function-handler
    """

    conn_lfm_handler = ConversationHandler(
        entry_points=[CommandHandler('connect', connect, block=False)],
        states={
            USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, username, block=False)
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_handle, block=False),
            MessageHandler(filters.COMMAND, cancel_handle, block=False),
        ],
    )

    return conn_lfm_handler
