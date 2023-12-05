#  Green Grass Bot — A program to notify about concerts of artists you listened to.
#  Copyright (C) 2021-2023 Ilia Baidakov <baidakovil@gmail.com>
#  This program is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software Foundation:
#  GPLv3 or any later version at your option. License: <https://www.gnu.org/licenses/>.
"""This file, like other in /commands, contains callback funcs for same name command."""

from telegram import Update
from telegram.ext import CallbackContext

from db.db import Db
from services.message_service import i34g, reply, up

db = Db()


async def help(update: Update, context: CallbackContext) -> None:
    """
    Callback function. Sends help message.
    Args:
        update, context: standart PTB callback signature
    """
    await db.save_user(update)
    user_id = up(update)
    await reply(
        update,
        await i34g('help.message', user_id=user_id),
        disable_web_page_preview=True,
    )
    return None
