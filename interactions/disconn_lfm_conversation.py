import logging

from telegram import ReplyKeyboardRemove
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import filters
from telegram.ext import MessageHandler

from db.db import Db
from interactions.utils import cancel_handle
from services.message_service import alChar
import services.logger

logger = logging.getLogger('A.dis')
logger.setLevel(logging.DEBUG)

db = Db()

DISC_ACC = 0

async def disconnect(update, context):
    """
    Entry point. Offers saved accounts to delete from database.
    #TODO Probably should be rewritten to single command handler.
    """
    userId = update.message.from_user.id
    lfmAccs = await db.rsql_lfmuser(userId)
    if lfmAccs:
        lfmAccs.append('Close')
        reply_keyboard = [lfmAccs]
        await update.message.reply_text(
            text='Choose lastfm\'s profile name to disconnect:',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True
            ))
        return DISC_ACC
    else:
        await update.message.reply_text('No lastm account saved \U0001F937')
        return ConversationHandler.END


async def disc_acc(update, context):
    """
    Second step. Waits for answer which account to delete.
    #TODO Probably should filter answers
    #TODO Command /cancel should work but it is not.
    """
    userId = update.message.from_user.id
    accToDisc = update.message.text
    if (accToDisc == '/cancel') or (accToDisc == 'Close'):
        mustDelete = await update.message.reply_text("Ok",reply_markup=ReplyKeyboardRemove())
        context.bot.deleteMessage(message_id = mustDelete.message_id,
                                chat_id = update.message.chat_id)
        return ConversationHandler.END
    rows_affected = await db.dsql_useraccs(userId, accToDisc)
    if rows_affected:
        text = f'Account _{accToDisc}_ deleted \U0000274E'
    else:
        text = f"Bot had waited for account name to disconnect, but _{accToDisc}_ \
not found. Try /disconnect again"
    await update.message.reply_text(
        text=alChar(text),
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='MarkdownV2')
    return ConversationHandler.END

def disconn_lfm_conversation():
    """
    Return conversation handler to add lastfm user.
    Probably could be rewritten to command handler.
    """
    states = {
        DISC_ACC: [MessageHandler(filters.TEXT, disc_acc)]
    }
    
    disconn_lfm_handler = ConversationHandler(
        entry_points=[CommandHandler('disconnect', disconnect)],
        states=states,
        fallbacks=[CommandHandler('cancel', cancel_handle)],
        allow_reentry=True,
        name="ggb_picklefile",
        persistent=False,
    )
    return disconn_lfm_handler