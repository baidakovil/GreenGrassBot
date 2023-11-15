from db.db import Db

db = Db()

from services.message_service import alChar #убрать

async def nolastfm(update, context):
    await db.save_user(update)
    await context.bot.send_message(
        chat_id=update.message.from_user.id,
        text=alChar(f"""
If you don't have *lastfm account*, just [register](https://www.last.fm/join/) one.\n\
It is free and great service since 2002.\n\
\U00002b07\n\
Add your *music service* like iTunes, Spotify, Yandex.Music, etc. to your new account \
in [settings](https://www.last.fm/settings/applications) of lastfm website.\n\
\U00002b07\n\
Press /connect. Enter account name and forget about the bot.\n\
\U00002705\n\
Bot will send you notification, when it find new concerts.\n
Notes:
• Bot work only with *public accounts* at this moment.\n\
• You can add accounts of your frinds or family members — and, may be, go to event together?
        """),
        parse_mode='MarkdownV2')