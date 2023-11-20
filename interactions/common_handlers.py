import logging

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from services.message_service import i34g, reply

logger = logging.getLogger('A.com')
logger.setLevel(logging.DEBUG)


async def cancel_handle(update: Update, context: CallbackContext) -> int:
    """
    Determine what to do when catched /cancel command: log, send message, return 0.
    Choose of return value is doubting =|.
    Args:
        update, context: standart PTB callback signature
    Returns:
        int = 0
    """
    user_id = update.message.from_user.id
    logger.info(f'User {user_id} canceled the conversation')
    await reply(update, await i34g('utils.cancel_message', user_id=user_id))
    return ConversationHandler.END


def error_handle(update: Update, context: CallbackContext) -> None:
    """
    Determine what to do when update causes error.
    """
    logger.warning(f'Update {update} caused error {context.error}')
    return None
