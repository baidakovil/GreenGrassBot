from db.db import Db
from services.message_service import alChar # убрать

db = Db()

async def start(update, context):
    await db.save_user(update)
    userId = update.message.from_user.id
    username = update.message.from_user.first_name
    lfmAccs = await db.rsql_lfmuser(userId)
    if not lfmAccs:
        startText = alChar(f"""
        Hello, {username}.\n\n\
\U00002753 To use the bot, make sure you have lastfm account and press /connect\n\n\
\U00002757 If you have no one, press /nolastfm for useful info\n\n\
\U00002764 Detailed info at /help
        """)
    else:
        lfmAccs = ['_' + acc + '_' for acc in lfmAccs]
        startText = alChar(f"""
        {username},\n
you have {len(lfmAccs)} accounts saved: {', '.join(lfmAccs)}.\n\
To add and delete accounts, use /connect and /disconnect.
        """)
    await context.bot.send_message(
        chat_id=userId,
        text=startText,
        parse_mode='MarkdownV2')
