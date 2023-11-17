import logging
from typing import Awaitable
import i18n

from telegram import InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from config import Cfg

logger = logging.getLogger('A.mes')
logger.setLevel(logging.DEBUG)

CFG = Cfg()


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
    text = alarm_char(text)
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
    text = alarm_char(text)
    return await context.bot.send_message(
        user_id,
        text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        disable_web_page_preview=disable_web_page_preview,
    )


def alarm_char(text: str, replace: bool = False) -> str:
    """
    Provides pre-escaping alarm characters in output messages with '/', accordin:
    core.telegram.org/bots/api#html-style. To distinguish markdown * and _ symbols, in
    i18n translates "technical replacing" is used, defined in this function in safety
    dict. With using replace=True, possible to do "technical replace" when needed in
    code.
    #########
    It is not beautiful and not sustainable decision, but it is simple decision. For
    replacing: changing of i18n.t class needed and/or change parse_mode to HTML.
    #########
    Args:
        text: text to replace alarm characters in OR character for techical replace
        replace: True if need to replace
    Returns:
        text to sent to user OR technical replace for symbol
    """
    safety = {
        '\u0277\u0277': '*',  #  \u0277 == ɷ
        '\u0278\u0278': '_',  #  \u0278 == ɸ
        '\u0283\u0283': '[',  #  \u0283 == ʃ
        '\u0285\u0285': ']',  #  \u0285 == ʅ
        '\u0272\u0272': '(',  #  \u0272 == ɲ
        '\u0273\u0273': ')',  #  \u0277 == ɳ
    }
    if replace:
        for safe, symb in safety.items():
            if symb == text:
                return safe
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
    for safe in safety:
        text = text.replace(safe, safety[safe])
    return text
