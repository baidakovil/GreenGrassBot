import logging
import services.logger

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

async def reply(update, text, markup=None, parse_mode='MarkdownV2'):
    """
    Replies a user with the given message.
    Args:
        update: default telegram arg
        text: text message to reply to user with
        markup: markup for showing buttons, defaults to none
        parse_mode: mode to parse the string, defaults to HTML
    """
    return await update.message.reply_text(text, reply_markup=markup, disable_web_page_preview=True,
                                           parse_mode=parse_mode)


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
    return await context.bot.send_message(user_id, text, reply_markup=markup, disable_web_page_preview=True,
                                          parse_mode=parse_mode)

def alChar(text):
    alarmCharacters = ('-', '.', '+', '!', '?', '"', '#')
    safetext = "".join(
        [c if c not in alarmCharacters else f'\\{c}' for c in text])
    return safetext