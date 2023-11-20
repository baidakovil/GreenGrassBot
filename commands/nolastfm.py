from telegram import Update
from telegram.ext import CallbackContext

from db.db import Db
from services.message_service import i34g
from services.message_service import reply

db = Db()


async def nolastfm(update: Update, context: CallbackContext) -> None:
    """
    Callback function. Sends help message about what to do if user don't have last.fm
    account.
    Args:
        update, context: standart PTB callback signature
    """
    await db.save_user(update)
    user_id = update.message.from_user.id
    await reply(update, await i34g('nolastfm.message', user_id=user_id))
    return None
