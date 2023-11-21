import logging
from typing import Dict

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from db.db import Db
from interactions.common_handlers import cancel_handle
from services.message_service import i34g, reply
from services.schedule_service import remove_jobs

logger = logging.getLogger('A.del')
logger.setLevel(logging.DEBUG)

db = Db()

DELETE_USER = 0


async def delete_answers(update: Update) -> Dict:
    """
    Return dict with localized answers for conversations.
    Args:
        update: update object
    Returns:
        dict{localized answer:what to do}
    """
    user_id = update.message.from_user.id
    answers = {
        await i34g("delete_user_conversation.yes", user_id=user_id): 'del',
        await i34g("delete_user_conversation.no", user_id=user_id): 'not_del',
        '/cancel': 'not_del',
    }
    return answers


async def delete(update: Update, context: CallbackContext) -> int:
    """
    Entry point. Offers to user 'Yes' and 'No' variants to delete it's userdata in bot.
    Args:
        update, context: standart PTB callback signature
    Returns:
        signals for stop or next step of the conversation
    """
    user_id = update.message.from_user.id
    if not await db.rsql_users(user_id=user_id):
        text = await i34g("delete_user_conversation.no_users", user_id=user_id)
        await reply(update, text, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    answers = await delete_answers(update)
    reply_markup = ReplyKeyboardMarkup(
        one_time_keyboard=True,
        resize_keyboard=True,
        keyboard=[list(answers.keys())],
    )
    text = await i34g("delete_user_conversation.choose", user_id=user_id)
    await reply(update, text, reply_markup=reply_markup)
    return DELETE_USER


async def delete_user(update: Update, context: CallbackContext) -> int:
    """
    Second step. Waits for answer wheter to delete user data
    Args:
        update, context: standart PTB callback signature
    Returns:
        signals for stop or next step of conversation
    """

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    answers = await delete_answers(update)
    answer = update.message.text
    if answer == '/cancel':
        #  Code of the condition only for removing keyboard
        del_msg = await update.message.reply_text(
            'ok', reply_markup=ReplyKeyboardRemove()
        )
        await context.bot.deleteMessage(
            message_id=del_msg.message_id, chat_id=update.message.chat_id
        )
        return ConversationHandler.END

    elif answer not in answers.keys():
        text = await i34g("delete_user_conversation.answer_not_found", user_id=user_id)

    elif answers[answer] == 'not_del':
        text = await i34g("delete_user_conversation.canceled", user_id=user_id)

    elif answers[answer] == 'del':
        locale = await db.rsql_locale(user_id)
        remove_jobs(user_id, chat_id, context)
        ####################################
        # Line below deletes all user data #
        ####################################
        result = await db.dsql_user(user_id)
        if result:
            text = await i34g("delete_user_conversation.deleted", locale=locale)
        else:
            text = await i34g("delete_user_conversation.error", user_id=user_id)

    await reply(update, text, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def delete_user_conversation() -> ConversationHandler:
    """
    Return conversation handler to delete user.
    """
    states = {DELETE_USER: [MessageHandler(filters.TEXT, delete_user)]}
    delete_user_handler = ConversationHandler(
        entry_points=[CommandHandler('delete', delete)],
        states=states,
        fallbacks=[CommandHandler('cancel', cancel_handle)],
    )
    return delete_user_handler
