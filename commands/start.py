from telegram import Update
from telegram.ext import CallbackContext

from db.db import Db
from services.message_service import i34g
from services.message_service import alarm_char
from services.message_service import reply

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
        text = await i34g('start.user', username=username, user_id=user_id)
    else:
        lfm_accs = ['_' + alarm_char(acc) + '_' for acc in lfm_accs]
        text = await i34g(
            'start.hacker',
            username=username,
            qty=len(lfm_accs),
            accs_noalarm=', '.join(lfm_accs),
            user_id=user_id,
        )
    await reply(update, text)
    return None
