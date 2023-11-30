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
