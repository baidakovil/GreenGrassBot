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
"""This file contains logic related to conversation started at /locale command."""

import logging
from typing import Dict

import i18n
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

logger = logging.getLogger('A.dis')
logger.setLevel(logging.DEBUG)

db = Db()

SET_LOCALE = 0


async def get_locale_codes(update: Update) -> Dict[str, str]:
    """
    Helper for conversation of language change. Note, that 'xx' in 'loc.xx' should be
    equal to language code for program logic.
    Args:
        update, context: standart PTB callback signature
    Returns:
        dictionary {locale name on user current language:locale code}
    """
    user_id = up(update)
    loc_codes = {
        await i34g('loc.en', user_id=user_id): 'en',
        await i34g('loc.ru', user_id=user_id): 'ru',
    }
    return loc_codes


async def locale(update: Update, context: CallbackContext) -> int:
    """
    Entry point. Offers to user possible locales to choose.
    """
    await db.save_user(update)
    user_id = up(update)
    loc_codes = await get_locale_codes(update)
    loc_names = list(loc_codes.keys())
    loc_names.append('/cancel')
    text = await i34g("loc.choose_lang", user_id=user_id)
    await reply(
        update,
        text,
        reply_markup=ReplyKeyboardMarkup(
            [loc_names],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return SET_LOCALE


async def set_locale(update: Update, context: CallbackContext) -> int:
    """
    Second step. Waits for answer which locale to choose and set it.
    """
    user_id, chat_id, new_loc_name, _ = up_full(update)
    prev_loc_code = await db.rsql_locale(user_id)
    loc_codes = await get_locale_codes(update)

    if new_loc_name == '/cancel':
        #  Code of the condition only for removing keyboard
        del_msg = await reply(update, 'ok', reply_markup=ReplyKeyboardRemove())
        await context.bot.deleteMessage(message_id=del_msg.message_id, chat_id=chat_id)
        return ConversationHandler.END

    elif new_loc_name not in loc_codes.keys():
        text = await i34g("loc.loc_not_found", loc=new_loc_name)
        await reply(update, text, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    elif prev_loc_code == loc_codes[new_loc_name]:
        text = await i34g("loc.choose_same_locale", loc=new_loc_name, user_id=user_id)
        await reply(update, text, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    else:
        new_loc_code = loc_codes[new_loc_name]
        affected = await db.wsql_settings(user_id=user_id, locale=new_loc_code)
        if affected:
            loc_codes = await get_locale_codes(update)
            i18n.set('locale', new_loc_code)
            new_loc_name = await i34g(f'loc.{new_loc_code}', locale=new_loc_code)
            text = await i34g(
                "loc.loc_changed",
                loc=new_loc_name,
                user_id=user_id,
            )
            logger.debug(
                f"User {user_id} changed loc to {new_loc_name}, code {new_loc_code}"
            )
        else:
            text = await i34g(
                "loc.error",
                acc=new_loc_name,
                user_id=user_id,
            )
            logger.warning(f"Error when {user_id} change locale to {new_loc_name}")

    await reply(update, text, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def locale_conversation() -> ConversationHandler:
    """
    Return conversation handler to change locale settings.
    """
    disconn_lfm_handler = ConversationHandler(
        entry_points=[CommandHandler('locale', locale)],
        states={SET_LOCALE: [MessageHandler(filters.TEXT, set_locale)]},
        fallbacks=[CommandHandler('cancel', cancel_handle)],
    )
    return disconn_lfm_handler
