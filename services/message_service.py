import logging
from typing import Awaitable, Tuple, Union

import i18n
from telegram import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, User
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from config import Cfg
from db.db import Db

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
        user_id, chat_id, message.text fields.

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
        reply_markup: inline keyboard attached to the message
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
        chat_id,
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
    text = "".join([c if c not in alarm_characters else f'\\{c}' for c in text])
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
            locale = CFG.DEFAULT_LOCALE
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
