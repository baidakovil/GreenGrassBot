import logging

from db.db import Db
from ui.news_builders import getNewsText

import services.logger
db = Db()

logger = logging.getLogger('A.det')
logger.setLevel(logging.DEBUG)

async def showNews(update, context):
    """
    Отправляет в чат список концертов исполнителя, выбранного командой '/xx'
    """
    userId = str(update.message.from_user.id)
    command = update.message.text
    shorthand = int(command[1:])
    newsText = await getNewsText(userId, shorthand, db)
    await update.message.reply_text(text=newsText, parse_mode='MarkdownV2', disable_web_page_preview=True)
    logger.info('newsText sent to ')