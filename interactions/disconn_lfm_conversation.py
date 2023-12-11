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
"""This file contains logic related to conversation started at /disconnect command."""

import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from db.db_service import Db, dsql_useraccs
from interactions.common_handlers import cancel_handle
from services.logger import logger
from services.message_service import i34g, reply, up, up_full
from services.schedule_service import remove_jobs

logger = logging.getLogger('A.dis')
logger.setLevel(logging.DEBUG)

db = Db()

DISC_ACC = 0


async def disconnect(update: Update, _context: CallbackContext) -> int:
    """
    Entry point. Offers to user saved accounts from database to delete, or replies about
    there is no accounts.
    Args:
        update, context: standart PTB callback signature
    Returns:
        signals for stop or next step of conversation
    """
    user_id = up(update)
    lfm_accs = await db.rsql_lfmuser(user_id)
    if lfm_accs:
        text = await i34g("disconn_lfm_conversation.choose_acc", user_id=user_id)
        lfm_accs.append('/cancel')
        lfm_accs = [[lfm_accs[i]] for i in range(len(lfm_accs))]
        await reply(
            update,
            text,
            reply_markup=ReplyKeyboardMarkup(
                lfm_accs,
                one_time_keyboard=True,
                resize_keyboard=True,
            ),
        )
        return DISC_ACC

    await reply(update, await i34g("disconn_lfm_conversation.no_accs", user_id=user_id))
    return ConversationHandler.END


async def disconn_lfm(update: Update, context: CallbackContext) -> int:
    """
    Second step. Waits for answer which account to delete, delete it, replies.
    Args:
        update, context: standart PTB callback signature
    Returns:
        signals for stop or next step of conversation
    """

    user_id, chat_id, acc, _ = up_full(update)
    acc = acc.lower()
    useraccs = await db.rsql_lfmuser(user_id)
    if acc not in useraccs:
        text = await i34g(
            "disconn_lfm_conversation.acc_not_found", acc=acc, user_id=user_id
        )
    else:
        affected_scr, affected_ua = await dsql_useraccs(db, user_id, acc)
        useraccs = await db.rsql_lfmuser(user_id)
        if not useraccs:
            remove_jobs(user_id, chat_id, context)
        if affected_scr and affected_ua:
            text = await i34g(
                "disconn_lfm_conversation.acc_scr_deleted", acc=acc, user_id=user_id
            )
            logger.info("User %s deleted account %s,scrobbles deleted", user_id, acc)
        elif affected_ua:
            text = await i34g(
                "disconn_lfm_conversation.acc_deleted", acc=acc, user_id=user_id
            )
            logger.info(
                "User %s deleted account %s, no scrobbles deleted", user_id, acc
            )
        else:
            text = await i34g(
                "disconn_lfm_conversation.error_when_del", acc=acc, user_id=user_id
            )
            logger.warning("Error when %s deleted account %s", user_id, acc)
    await reply(update, text, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def disconn_lfm_conversation() -> ConversationHandler:
    """
    Returns conversation handler to add lastfm user.
    """
    disconn_lfm_handler = ConversationHandler(
        entry_points=[CommandHandler('disconnect', disconnect, block=False)],
        states={
            DISC_ACC: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, disconn_lfm, block=False
                )
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_handle, block=False),
            MessageHandler(filters.COMMAND, cancel_handle, block=False),
        ],
    )
    return disconn_lfm_handler
