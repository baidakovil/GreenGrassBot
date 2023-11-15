import logging

import i18n
from telegram import ReplyKeyboardRemove
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext import MessageHandler

from db.db import Db
from interactions.utils import cancel_handle
from services.message_service import reply

logger = logging.getLogger('A.dis')
logger.setLevel(logging.DEBUG)

db = Db()

DISC_ACC = 0


async def disconnect(update, context) -> int:
    """
    Entry point. Offers to user saved accounts from database to delete,
    or replies about there is no accounts.
    """
    userId = update.message.from_user.id
    lfmAccs = await db.rsql_lfmuser(userId)
    if lfmAccs:
        text = i18n.t("disconn_lfm_conversation.choose_acc")
        lfmAccs.append('Close')
        await reply(
            update,
            text,
            reply_markup=ReplyKeyboardMarkup(
                [lfmAccs],
                one_time_keyboard=True,
                resize_keyboard=True,
            ))
        return DISC_ACC
    else:
        await reply(update, i18n.t("disconn_lfm_conversation.no_accs"))
        return ConversationHandler.END


async def disconn_lfm(update, context) -> int:
    """
    Second step. Waits for answer which account to delete, delete it it is, replies.
    """
    user_id = update.message.from_user.id
    acc = update.message.text.lower()
    if acc in ('/cancel', 'close'):
        #  Code of the condition only for removing keyboard
        del_msg = await update.message.reply_text('ok',
                                                  reply_markup=ReplyKeyboardRemove())
        await context.bot.deleteMessage(message_id=del_msg.message_id,
                                        chat_id=update.message.chat_id)
        await context.bot.deleteMessage(message_id=update.message.message_id,
                                        chat_id=update.message.chat_id)
        return ConversationHandler.END
    rows_affected = await db.dsql_useraccs(user_id, acc)
    if rows_affected:
        text = i18n.t("disconn_lfm_conversation.acc_deleted", acc=acc)
    else:
        text = i18n.t("disconn_lfm_conversation.acc_not_found", acc=acc)
    await reply(update, text, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def disconn_lfm_conversation() -> ConversationHandler:
    """
    Return conversation handler to add lastfm user.
    Probably could be rewritten to command handler.
    """
    states = {
        DISC_ACC: [MessageHandler(filters.TEXT, disconn_lfm)]
    }
    disconn_lfm_handler = ConversationHandler(
        entry_points=[CommandHandler('disconnect', disconnect)],
        states=states,
        fallbacks=[CommandHandler('cancel', cancel_handle)],
    )
    return disconn_lfm_handler
