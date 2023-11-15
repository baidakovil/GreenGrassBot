import i18n
from telegram import Update
from telegram.ext import CallbackContext

from db.db import Db
from services.message_service import reply

db = Db()


async def nolastfm(update: Update, context: CallbackContext) -> None:
    """
    Sends help message about what to do if user don't have last.fm account.
    """
    await db.save_user(update)
    await reply(update, i18n.t('nolastfm.message'))
    return None