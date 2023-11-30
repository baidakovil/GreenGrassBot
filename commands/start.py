from telegram import Message, Update, User
from telegram.ext import CallbackContext

from config import Cfg
from db.db import Db
from services.message_service import alarm_char, i34g, reply, send_message, up_full

db = Db()
CFG = Cfg()


async def start(update: Update, context: CallbackContext) -> None:
    """
    Callback function. Sends start message. Alarms developer. If user have accounts,
    list it.
    Args:
        update, context: standart PTB callback signature
    """
    user_id, _, _, username = up_full(update)
    await db.save_user(update)
    if CFG.NEW_USER_ALARMING:
        await send_message(
            context, CFG.DEVELOPER_CHAT_ID, text=f'New user: {user_id}, {username}'
        )
    lfm_accs = await db.rsql_lfmuser(user_id)
    if not lfm_accs:
        pretext = await i34g('start.user', user_id=user_id)
    else:
        lfm_accs = ['_' + alarm_char(acc) + '_' for acc in lfm_accs]
        pretext = await i34g(
            'start.hacker',
            accs_noalarm=', '.join(lfm_accs),
            user_id=user_id,
        )
    message = await i34g('start.message', user_id=user_id, qty=CFG.MAX_LFM_ACCOUNT_QTY)
    text = pretext + message
    await reply(update, text)
    return None
