import main
import logging
import asyncio
from datetime import datetime
from config import Cfg

from db import ArtScrobble, Event, User, UserSettings
from db import Db
from db import timestamp_to_text, date_to_text
from gglib2 import getInfoText, getNewsText


logger = logging.getLogger('A.D')
logger.setLevel(logging.DEBUG)

CFG = Cfg()

u1 = User(
    user_id = 144297913,
    username = 'baidakovil',
    first_name = 'Ilya',
    last_name = 'Baidakov',
    language_code = 'en',
    reg_datetime=date_to_text(datetime.now())
    )

u2 = User(
    user_id = 123456789,
    username = 'badbondarienko',
    first_name = 'Bad',
    last_name = 'Bondarienko',
    language_code = 'ru',
    )

db = Db(
    dbpath='db',
    dbname='ggb_sqlite.db',
    script_pathname='db/create_tables_script.sql',
    hard_rewrite=True,
)

# Users press '/connect' or '/start'
asyncio.run(db.wsql_users(u1))
asyncio.run(db.wsql_users(u2))

# Users add lfm account
print(asyncio.run(db.wsql_useraccs(u1.user_id, 'badbaidakov')))
print(asyncio.run(db.wsql_useraccs(u1.user_id, 'badbaidakov')))
print(asyncio.run(db.wsql_useraccs(u1.user_id, 'mir__')))
print(asyncio.run(db.wsql_useraccs(u1.user_id, 'LarsVsNapster')))

# asyncio.run(db.wsql_settings(u1.user_id, min_listens=10))

infoText = getInfoText(u1.user_id, db)
print(infoText)

shorthand = 7

newsText = getNewsText(u1.user_id, shorthand, db)

print(newsText)