import i18n

from db.db import Db
from services.message_service import reply

db = Db()


async def start(update, context) -> None:
    """
    Sends start message. If user have accounts, list it.
    """
    await db.save_user(update)
    user_id = update.message.from_user.id
    username = update.message.from_user.first_name
    lfm_accs = await db.rsql_lfmuser(user_id)
    if not lfm_accs:
        text = i18n.t('start.user', username=username)
    else:
        lfm_accs = ['_' + acc + '_' for acc in lfm_accs]
        text = i18n.t('start.hacker',
                      username=username,
                      qty=len(lfm_accs),
                      accs=', '.join(lfm_accs),
                      )
    await reply(update, text)
    return None
