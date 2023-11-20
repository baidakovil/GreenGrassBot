from telegram import Update
from telegram.ext import CallbackContext

from db.db import Db
from services.message_service import i34g
from services.message_service import reply

db = Db()


async def nonewevents(update: Update, context: CallbackContext) -> None:
    """
    Callback function. Toggle 'nonewevents' settings on-off. This settings controls
    whether user should be notified when no events there.
    Args:
        update, context: standart PTB callback signature
    """
    user_id = update.message.from_user.id
    usersettings = await db.rsql_settings(user_id)
    if not usersettings:
        text = await i34g('nonewevents.error', user_id=user_id)
        await reply(update, text)
        return None

    new_value = int(not bool(usersettings.nonewevents))
    affected = await db.wsql_settings(user_id=user_id, nonewevents=new_value)
    if affected and new_value:
        text = await i34g('nonewevents.nots_disabled', user_id=user_id)
    elif affected:
        text = await i34g('nonewevents.nots_enabled', user_id=user_id)
    else:
        text = await i34g('nonewevents.error', user_id=user_id)
    await reply(update, text)
    return None
