import logging
from numpy import diag

from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext import MessageHandler

from db.db import Db
from interactions.utils import cancel_handle
from services.message_service import alChar
from services.parse_services import check_valid_lfm
from services.schedule_service import runsearch
from services.schedule_service import remove_job_if_exists
from config import Cfg

logger = logging.getLogger('A.con')
logger.setLevel(logging.DEBUG)

db = Db()
CFG = Cfg()

USERNAME, RUNSEARCH = 0, 1

async def connect(update, context):
    """
    Entry point. Asks the lastfm username.
    Stop conversation if max acc qty reached. 
    """
    logger.debug('Entered to connect()')
    await db.save_user(update)
    userId = update.message.from_user.id
    useraccs = await db.rsql_lfmuser(user_id=userId)
    if len(useraccs) >= CFG.MAX_LFM_ACCOUNT_QTY:
        await update.message.reply_text(f'Sorry, maximum {CFG.MAX_LFM_ACCOUNT_QTY} accounts possible at the moment. Use /disconnect to remove accounts.')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Enter lastfm\'s profile name:')
        return USERNAME

async def username(update, context):
    """
    Second step. Gets lastfm username and check it. Variants possible:
    a) Name already in db -> Message -> END
    b) Name give 403/404/other error -> Message -> END
    c) Ok in lastfm -> Message -> RUNSEARCH
    """
    logger.debug('Entered to username()')
    userId = update.message.from_user.id
    lastfmUser = update.message.text
    useraccs = await db.rsql_lfmuser(userId)
    
    if lastfmUser in useraccs:
        await update.message.reply_text(f'Sorry, you already have _{lastfmUser}_ account')
        return ConversationHandler.END
    
    acc_valid, diagnosis = check_valid_lfm(userId, lastfmUser, db)
    if not acc_valid:
        await update.message.reply_text(
            text=alChar(diagnosis),
            parse_mode='MarkdownV2')
        return ConversationHandler.END
    
    affected = await db.wsql_useraccs(userId, lastfmUser)
    if affected == 1:
        text = f'Account _{lastfmUser}_ added \U00002705'
    else:
        await update.message.reply_text(
            text=alChar('Something wrong when added account'),
            parse_mode='MarkdownV2')
    if len(await db.rsql_lfmuser(userId)) == 1:
        text += f'\n\nBot will notify you each day at {CFG.DEFAULT_NOTICE_TIME[:5]} UTC \
if there is new events.\nPress /getevents to check events anytime you want'
    await update.message.reply_text(
        text=alChar(text),
        parse_mode='MarkdownV2')
    return ConversationHandler.END
    logger.info(f"User with user_id: {userId} added lfm account: {lastfmUser}")

def conn_lfm_conversation():
    """
    Return conversation handler to add lastfm user.
    Probably could be rewritten to command handler.
    """

    states = {
        USERNAME: [MessageHandler(filters.TEXT, username)],
        RUNSEARCH: [MessageHandler(filters.TEXT, runsearch)],
    }
    conn_lfm_handler = ConversationHandler(
        entry_points=[CommandHandler('connect', connect)],
        states=states,
        fallbacks=[CommandHandler('cancel', cancel_handle)],
        allow_reentry=True,
        name="ggb_picklefile",
        persistent=True,
    )

    return conn_lfm_handler