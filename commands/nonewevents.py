from db.db import Db

db = Db()

async def nonewevents(update, context):
    userId = update.message.from_user.id
    usersettings = await db.rsql_settings(userId)
    new_value = int(not bool(usersettings.nonewevents))
    affected = await db.wsql_settings(userId, nonewevents=new_value)
    if affected and new_value:
        text = f'\U0001F60F Notifications like *No new events* disabled'
    elif affected:
        text = f'Notifications like *No new events* enabled \U0001F60C'
    else:
        text = f'Settings was not updated'
    await update.message.reply_text(text, parse_mode='MarkdownV2')