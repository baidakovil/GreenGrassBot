import logging
from numpy import diag

import i18n
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext import MessageHandler
from telegram import Update
from telegram.ext import CallbackContext

from db.db import Db
from interactions.utils import cancel_handle
from services.message_service import reply
from services.parse_services import check_valid_lfm
from services.schedule_service import run_daily
from config import Cfg

logger = logging.getLogger('A.con')
logger.setLevel(logging.DEBUG)

db = Db()
CFG = Cfg()

USERNAME = 0


async def connect(update: Update, context: CallbackContext) -> int:
    """
    Entry point. Asks the lastfm username. Stop conversation if max acc qty reached by
    user.
    Args:
        update, context: standart PTB callback signature
    Returns:
        signals for stop or next step of conversation
    """
    logger.debug('Entered to connect()')
    await db.save_user(update)
    user_id = update.message.from_user.id
    useraccs = await db.rsql_lfmuser(user_id=user_id)
    if len(useraccs) >= CFG.MAX_LFM_ACCOUNT_QTY:
        await reply(
            update,
            i18n.t(
                'conn_lfm_conversation.max_acc_reached', qty=CFG.MAX_LFM_ACCOUNT_QTY
            ),
        )
        return ConversationHandler.END
    else:
        await reply(update, i18n.t('conn_lfm_conversation.enter_lfm'))
        return USERNAME


async def username(update: Update, context: CallbackContext) -> int:
    """
    Second step. Gets lastfm username and check it. Variants possible: a) Name already
    in db -> Message -> END b) Name give 403/404/other error -> Message -> END c) Ok in
    lastfm and added -> Message -> RUNSEARCH.
    Args:
        update, context: standart PTB callback signature
    Returns:
        signals for stop or next step of conversation
    """
    logger.debug('Entered to username()')
    user_id = update.message.from_user.id
    acc = update.message.text
    useraccs = await db.rsql_lfmuser(user_id)
    if acc in useraccs:
        await reply(update, i18n.t('conn_lfm_conversation.already_have', acc=acc))
        return ConversationHandler.END

    acc_valid, diagnosis = check_valid_lfm(acc)
    if not acc_valid:
        await reply(update, diagnosis)
        logger.info(
            f'User with user_id: {user_id} trying to added lfm account:  {acc} but acc is not valid'
        )
        return ConversationHandler.END

    affected_rows = await db.wsql_useraccs(user_id, acc)
    if affected_rows == 1:
        text = i18n.t('conn_lfm_conversation.done', acc=acc)
        if len(await db.rsql_lfmuser(user_id)) == 1:
            text += i18n.t(
                'conn_lfm_conversation.alarm_info', time=CFG.DEFAULT_NOTICE_TIME[:5]
            )
        await run_daily(update, context)
        await reply(update, text)
        logger.info(f'User: {user_id} have added lfm account:  {acc}')
    else:
        await reply(update, i18n.t('conn_lfm_conversation.some_error'))
        logger.info(f'User: {user_id} tried to add lfm acc: {acc} but ended with error')
    return ConversationHandler.END


def conn_lfm_conversation() -> ConversationHandler:
    """
    Function-placeholder for returning conversation handler to add lastfm user.
    Returns:
        function-handler
    """
    states = {
        USERNAME: [MessageHandler(filters.TEXT, username)],
    }
    conn_lfm_handler = ConversationHandler(
        entry_points=[CommandHandler('connect', connect)],
        states=states,
        fallbacks=[CommandHandler('cancel', cancel_handle)],
    )

    return conn_lfm_handler
