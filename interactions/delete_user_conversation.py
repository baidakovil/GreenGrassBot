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
"""This file contains logic related to conversation started at /delete command."""

import logging
from typing import Dict

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

import config as cfg
from db.db_service import Db, dsql_user
from interactions.common_handlers import cancel_handle
from services.logger import logger
from services.message_service import i34g, reply, up, up_full
from services.schedule_service import remove_jobs

logger = logging.getLogger('A.del')
logger.setLevel(logging.DEBUG)


db = Db()

DELETE_USER = 0


async def delete_answers(update: Update) -> Dict:
    """
    Return dict with localized answers for conversations.
    Args:
        update: update object
    Returns:
        dict{localized answer:what to do}
    """
    user_id = up(update)
    answers = {
        await i34g("delete_user_conversation.yes", user_id=user_id): 'del',
        await i34g("delete_user_conversation.no", user_id=user_id): 'not_del',
        '/cancel': 'not_del',
    }
    return answers


async def delete(update: Update, _context: CallbackContext) -> int:
    """
    Entry point. Offers to user 'Yes' and 'No' variants to delete it's userdata in bot.
    Args:
        update, context: standart PTB callback signature
    Returns:
        signals for stop or next step of the conversation
    """
    user_id = up(update)
    if not await db.rsql_users(user_id=user_id):
        assert update.message
        assert update.message.from_user
        locale = update.message.from_user.language_code
        if locale is None:
            locale = cfg.LOCALE_DEFAULT
        text = await i34g("delete_user_conversation.no_users", locale=locale)
        await reply(update, text, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    answers = await delete_answers(update)
    reply_markup = ReplyKeyboardMarkup(
        one_time_keyboard=True,
        resize_keyboard=True,
        keyboard=[list(answers.keys())],
    )
    text = await i34g("delete_user_conversation.choose", user_id=user_id)
    await reply(update, text, reply_markup=reply_markup)
    return DELETE_USER


async def delete_user(update: Update, context: CallbackContext) -> int:
    """
    Second step. Waits for answer wheter to delete user data
    Args:
        update, context: standart PTB callback signature
    Returns:
        signals for stop or next step of conversation
    """
    user_id, chat_id, answer, _ = up_full(update)
    answers = await delete_answers(update)
    text = ''
    if answer not in answers.keys():
        text = await i34g("delete_user_conversation.answer_not_found", user_id=user_id)
    elif answers[answer] == 'not_del':
        text = await i34g("delete_user_conversation.canceled", user_id=user_id)
    elif answers[answer] == 'del':
        locale = await db.rsql_locale(user_id)
        locale = cfg.LOCALE_DEFAULT if locale is None else locale
        remove_jobs(user_id, chat_id, context)
        ####################################
        # Line below deletes all user data #
        ####################################
        result = await dsql_user(db, user_id)
        if result:
            text = await i34g("delete_user_conversation.deleted", locale=locale)
        else:
            text = await i34g("delete_user_conversation.error", user_id=user_id)
    await reply(update, text, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def delete_user_conversation() -> ConversationHandler:
    """
    Return conversation handler to delete user.
    """
    delete_user_handler = ConversationHandler(
        entry_points=[CommandHandler('delete', delete, block=False)],
        states={
            DELETE_USER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, delete_user, block=False
                )
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_handle, block=False),
            MessageHandler(filters.COMMAND, cancel_handle, block=False),
        ],
    )
    return delete_user_handler
