# Green Grass Bot — A program to notify about concerts of artists you listened to.
# Copyright (C) 2021-2023 Ilia Baidakov <baidakovil@gmail.com>

# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <https://www.gnu.org/licenses/>.
"""This file contains callback functions for auxiliary handlers."""

import html
import json
import logging
import traceback

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ContextTypes, ConversationHandler

from config import Cfg
from services.logger import logger
from services.message_service import i34g, reply, send_message, up

logger = logging.getLogger(name='A.com')
logger.setLevel(logging.DEBUG)

CFG = Cfg()


async def cancel_handle(update: Update, context: CallbackContext) -> int:
    """
    Determine what to do when catched /cancel command: log, send message, return 0.
    Choose of return value is doubting =|.
    Args:
        update, context: standart PTB callback signature
    Returns:
        int = 0
    """
    user_id = up(update)
    logger.info(f'BotUser {user_id} canceled the conversation')
    await reply(update, await i34g('common_handlers.cancel_message', user_id=user_id))
    return ConversationHandler.END


async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle unknown commands.
    """
    user_id = up(update)
    await reply(update, await i34g("common_handlers.unknown_command", user_id=user_id))


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Log the error and send a telegram message to notify the developer. Source:
    docs.python-telegram-bot.org/en/v20.6/examples.errorhandlerbot.html
    """
    assert context.error
    logger.warning(f'Update {update} caused error {context.error}')
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    logger.warning(f'ERROR HANDLER MESSAGE: {message}')

    await send_message(
        context,
        chat_id=CFG.DEVELOPER_CHAT_ID,
        text=message[:4095],
        parse_mode=ParseMode.HTML,
    )
