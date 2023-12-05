#  Green Grass Bot — A program to notify about concerts of artists you listened to.
#  Copyright (C) 2021-2023 Ilia Baidakov <baidakovil@gmail.com>
#  This program is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software Foundation:
#  GPLv3 or any later version at your option. License: <https://www.gnu.org/licenses/>.
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

from db.db import Db
from interactions.common_handlers import cancel_handle
from services.logger import logger
from services.message_service import i34g, reply, up, up_full
from services.schedule_service import remove_jobs

logger = logging.getLogger('A.dis')
logger.setLevel(logging.DEBUG)

db = Db()

DISC_ACC = 0


async def disconnect(update: Update, context: CallbackContext) -> int:
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
        await reply(
            update,
            text,
            reply_markup=ReplyKeyboardMarkup(
                [lfm_accs],
                one_time_keyboard=True,
                resize_keyboard=True,
            ),
        )
        return DISC_ACC
    else:
        await reply(
            update, await i34g("disconn_lfm_conversation.no_accs", user_id=user_id)
        )
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
    if acc == '/cancel':
        #  Code of the condition only for removing keyboard
        del_msg = await reply(update, 'ok', reply_markup=ReplyKeyboardRemove())
        await context.bot.deleteMessage(message_id=del_msg.message_id, chat_id=chat_id)
        return ConversationHandler.END
    elif acc not in useraccs:
        text = await i34g(
            "disconn_lfm_conversation.acc_not_found", acc=acc, user_id=user_id
        )
    else:
        affected_scr, affected_ua = await db.dsql_useraccs(user_id, acc)
        useraccs = await db.rsql_lfmuser(user_id)
        if not useraccs:
            remove_jobs(user_id, chat_id, context)
        if affected_scr and affected_ua:
            text = await i34g(
                "disconn_lfm_conversation.acc_scr_deleted", acc=acc, user_id=user_id
            )
            logger.info(f"BotUser {user_id} deleted account {acc},scrobbles deleted")
        elif affected_ua:
            text = await i34g(
                "disconn_lfm_conversation.acc_deleted", acc=acc, user_id=user_id
            )
            logger.info(
                f"BotUser {user_id} deleted account {acc}, no scrobbles deleted"
            )
        else:
            text = await i34g(
                "disconn_lfm_conversation.error_when_del", acc=acc, user_id=user_id
            )
            logger.warning(f"Error when {user_id} deleted account {acc}")
    await reply(update, text, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def disconn_lfm_conversation() -> ConversationHandler:
    """
    Returns conversation handler to add lastfm user.
    """
    disconn_lfm_handler = ConversationHandler(
        entry_points=[CommandHandler('disconnect', disconnect)],
        states={DISC_ACC: [MessageHandler(filters.TEXT, disconn_lfm)]},
        fallbacks=[CommandHandler('cancel', cancel_handle)],
    )
    return disconn_lfm_handler
