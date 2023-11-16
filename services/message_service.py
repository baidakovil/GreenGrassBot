import logging

from config import Cfg

logger = logging.getLogger('A.mes')
logger.setLevel(logging.DEBUG)

CFG = Cfg()


def parse_placeholders(string, keys, values):
    """
    Parses placeholders within a string.
    Args:
        keys: placeholder keys being used
        values: values to replaced the keys with
    """
    for i in range(0, len(keys)):
        string = string.replace(keys[i], values[i])
    return string


async def reply(update, text, parse_mode='MarkdownV2', reply_markup=None, disable_web_page_preview=False):
    """
    Replies a user with the given message.
    Args:
        update: default telegram arg
        text: text message to reply to user with
        markup: markup for showing buttons, defaults to none
        parse_mode: mode to parse the string, defaults to HTML
    """
    text = alarm_char(text)
    return await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode, disable_web_page_preview=disable_web_page_preview)


async def send_message(context, user_id, text, markup=None, parse_mode='MarkdownV2'):
    """
    Sends a message to the user with the given id.
    Args:
        context: default telegram arg
        user_id: id of user to send message to
        text: text message to send user
        markup: markup for showing buttons, defaults to none
        parse_mode: mode to parse the string, defaults to HTML
    """
    return await context.bot.send_message(user_id, text, reply_markup=markup, disable_web_page_preview=True, parse_mode=parse_mode)


def alarm_char(text):
    """
    Add preceeding / to alarm characters according https://core.telegram.org/bots/api#html-style
    Args:
        text: text to insert / for.
    Returns:
        text with inserted / before alarmc characters.
    """
    alarm_characters = ('-', '.', '+', '!', '?', '"', '#')
    safetext = "".join(
        [c if c not in alarm_characters else f'\\{c}' for c in text])
    return safetext
    """
    #TODO: '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'  AND Proper markdown escaping

    """
