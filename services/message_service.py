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
"""This file contains functions related to text messages: reading, sending, i18n."""

import logging
from typing import Awaitable, Tuple, Union

import i18n
from telegram import (
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    User,
)
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from config import Cfg
from db.db import Db
from services.logger import logger

logger = logging.getLogger('A.mes')
logger.setLevel(logging.DEBUG)

CFG = Cfg()

db = Db()


def up_full(update: Update) -> Tuple[int, int, str, str]:
    """
    Function to handle updates. Aims:
    a) simple type hints
    b) debugging through logging of possible bot fails through unappropriate updates.
    Now it is assumed that every update contains message, text and is from user.
    Args:
        update: update object
    Returns:
        user_id, chat_id, message.text, first_name fields

    # TODO should I use effective chat?
    # TODO should I rewrite user_id to chat_id everywhere?
    """

    user_id = 0
    chat_id = 0
    text = ''
    first_name = ''

    if isinstance(update.message, Message):
        chat_id = update.message.chat_id
        text = update.message.text
        if isinstance(update.message.from_user, User):
            user_id = update.message.from_user.id
            first_name = update.message.from_user.first_name
        else:
            logger.warning(f'UPDATE IS NOT FROM USER. Probably bot will fail')
    else:
        logger.warning(f'UPDATE IS NOT A MESSAGE. Probably bot will fail')
    if not isinstance(text, str):
        logger.warning(f'UPDATE DOES NOT CONTAIN TEXT. Probably bot will fail')
        text = ''

    return user_id, chat_id, text, first_name


def up(update: Update) -> int:
    """
    Same as up_full, but for only single variable user_id.
    """
    user_id = 0
    if isinstance(update.message, Message):
        if isinstance(update.message.from_user, User):
            user_id = update.message.from_user.id
        else:
            logger.warning(f'UPDATE IS NOT FROM USER. Probably bot will fail')
    return user_id


async def reply(
    update: Update,
    text: str,
    parse_mode: str = ParseMode.MARKDOWN_V2,
    reply_markup: Union[ReplyKeyboardMarkup, ReplyKeyboardRemove, None] = None,
    disable_web_page_preview: bool = False,
) -> Message:
    """
    Replies to user basing on update object.
    Args:
        update: Tg update object
        text: text message to reply
        parse_mode: mode to parse the string
        reply_markup: what to do with keyboard
        disable_web_page_preview: show preview or not, OVERRIDING default true
    """
    assert update.message
    return await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        disable_web_page_preview=disable_web_page_preview,
    )


async def send_message(
    context: CallbackContext,
    chat_id: int,
    text: str,
    parse_mode: str = ParseMode.MARKDOWN_V2,
    reply_markup: Union[ReplyKeyboardMarkup, ReplyKeyboardRemove, None] = None,
    disable_web_page_preview: bool = False,
) -> Message:
    """
    Sends a message basing on user_id object.
    Args:
        context: default telegram arg
        user_id: id of user to send message to
        text: text message to send user
        reply_markup: what to do with keyboard
        parse_mode: mode to parse the string
    """
    return await context.bot.send_message(
        chat_id,
        text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        disable_web_page_preview=disable_web_page_preview,
    )


def alarm_char(text: Union[str, int], escape='\\') -> str:
    """
    Provides pre-escaping alarm characters in output messages with '/', accordin:
    core.telegram.org/bots/api#html-style.
    Args:
        *args: single argument, i18n translation link e.g. "loc.choose_lang"
        **kwargs: dict with i18n values for placeholders
    """
    text = str(text)
    alarm_characters = (
        '_',
        '*',
        '[',
        ']',
        '(',
        ')',
        '~',
        '`',
        '>',
        '#',
        '+',
        '-',
        '=',
        '|',
        '{',
        '}',
        '.',
        '!',
    )
    text = "".join([c if c not in alarm_characters else f'{escape}{c}' for c in text])
    return text


async def i34g(*args: str, **kwargs: Union[str, int]) -> str:
    """
    Internatiolization and escaping. Determines current locale. Prepares proper
    localized text. Please see alarm_char() definition for clearings. Note, that alarm
    characters in translations should be pre-escaped manually.
    Args:
        args: single positional argument like "loc.choose_lang", is code of i18n
        kwargs: keyword arguments, including
            placeholders: i18n-placeholders with names according JSON-translation. Those
            ended with "_noalarm" will be passed to Tg without escaping
            user_id: user_id for locale setting reading
            locale: locale, when appropriated (for url or when deleting account)
    Returns:
        text prepared to send
    """
    if 'locale' not in kwargs.keys():
        user_id = int(kwargs.pop('user_id'))
        locale = await db.rsql_locale(user_id=user_id)
        if locale is None:
            logger.warning('Can not read locale settings. It should not be like this!')
            locale = CFG.LOCALE_DEFAULT
        kwargs['locale'] = locale

    kwargs = {
        arg: kwargs[arg] if arg.endswith('_noalarm') else alarm_char(kwargs[arg])
        for arg in kwargs.keys()
    }

    text = i18n.t(*args, **kwargs)

    if not isinstance(text, str):
        logger.warning('Error when reading translation')
        return str(text)
    else:
        return text


def preescape_file(filename: str) -> str:
    """
    Utility to prepare human-readable text for using with i18n and i34g functions. Don't
    forget to remove \\ before technical symbols, by own hand.
    Args:
        filename: path to file with text
    Returns:
        Nothing, but add preescaped text below
    """

    with open(filename, 'r') as file:
        escaped = alarm_char(file.read(), escape='\\\\')
    escaped = escaped.replace('\n', '\\n')

    with open(filename, 'a') as file:
        file.write(f'\n{"-"*15}\n')
        file.write(escaped)

    return escaped
