import logging
from typing import Awaitable, Union

import i18n
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from config import Cfg
from db.db import Db

logger = logging.getLogger('A.mes')
logger.setLevel(logging.DEBUG)

CFG = Cfg()

db = Db()


async def reply(
    update: Update,
    text: str,
    parse_mode: str = 'MarkdownV2',
    reply_markup: InlineKeyboardMarkup = None,
    disable_web_page_preview: bool = False,
) -> Awaitable:
    """
    Replies to user basing on update object.
    Args:
        update: Tg update object
        text: text message to reply
        parse_mode: mode to parse the string
        reply_markup: inline keyboard attached to the message
        disable_web_page_preview: show preview or not, OVERRIDING default true
    """
    return await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        disable_web_page_preview=disable_web_page_preview,
    )


async def send_message(
    context: CallbackContext,
    user_id: int,
    text: str,
    parse_mode: str = 'MarkdownV2',
    reply_markup: InlineKeyboardMarkup = None,
    disable_web_page_preview: bool = False,
) -> Awaitable:
    """
    Sends a message basing on user_id object.
    Args:
        context: default telegram arg
        user_id: id of user to send message to
        text: text message to send user
        reply_markup: inline keyboard attached to the message
        parse_mode: mode to parse the string, defaults to HTML
    """
    return await context.bot.send_message(
        user_id,
        text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        disable_web_page_preview=disable_web_page_preview,
    )


def alarm_char(text: Union[str, int]) -> str:
    """
    Provides pre-escaping alarm characters in output messages with '/', accordin:
    core.telegram.org/bots/api#html-style.
    Args:
        *args: single argument, i18n translation link e.g. "utils.cancel_message"
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
    text = "".join([c if c not in alarm_characters else f'\\{c}' for c in text])
    return text


async def i34g(*args: str, **kwargs: str) -> str:
    """
    Internatiolization and escaping. Define curren user language. Prepare text to send
    to user. See alarm_char() definition for clearings. Alarm characters in translations
    should be pre-escaped manually. Import of db included to avoid circular import.
    Args:
        args: single positional argument like "utils.cancel_message", is code of i18n
        kwargs: keyword arguments, including
            placeholders: i18n-placeholders with names and quantities according
            JSON-translation. Ended with "_noalarm" passed to Tg without escaping
            user_id: user_id to read locale setting
            locale: locale, when appropriated (for url)
    Returns:
        text prepared to send
    """
    if 'locale' not in kwargs.keys():
        kwargs['locale'] = await db.rsql_locale(user_id=kwargs.pop('user_id'))

    kwargs = {
        arg: kwargs[arg] if arg.endswith('_noalarm') else alarm_char(kwargs[arg])
        for arg in kwargs.keys()
    }
    text = i18n.t(*args, **kwargs)
    return text
