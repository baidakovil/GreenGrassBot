import i18n
from telegram import Update
from telegram.ext import CallbackContext

from db.db import Db
from services.message_service import reply
from services.message_service import alarm_char

db = Db()


async def start(update: Update, context: CallbackContext) -> None:
    """
    Callback function. Sends start message. If user have accounts, list it.
    Args:
        update, context: standart PTB callback signature
    """
    await db.save_user(update)
    user_id = update.message.from_user.id
    username = update.message.from_user.first_name
    lfm_accs = await db.rsql_lfmuser(user_id)
    if not lfm_accs:
        text = i18n.t('start.user', username=username)
    else:
        undscr = alarm_char('_', replace=True)
        lfm_accs = [undscr + acc + undscr for acc in lfm_accs]
        text = i18n.t(
            'start.hacker',
            username=username,
            qty=len(lfm_accs),
            accs=', '.join(lfm_accs),
        )
    await reply(update, text)
    return None
