import i18n

from db.db import Db
from services.message_service import reply

db = Db()

async def nonewevents(update, context) -> None:
    """
    Toggle 'nonewevents' settings on-off.
    This settings controls whether user should be notified when no events there. 
    """
    userId = update.message.from_user.id
    usersettings = await db.rsql_settings(userId)
    new_value = int(not bool(usersettings.nonewevents))
    affected = await db.wsql_settings(userId, nonewevents=new_value)
    if affected and new_value:
        text = i18n.t('nonewevents.nots_disabled')
    elif affected:
        text = i18n.t('nonewevents.nots_enabled')
    else:
        text = i18n.t('nonewevents.error')
    await reply(update, text)
    return None