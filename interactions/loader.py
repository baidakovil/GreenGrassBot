import logging

from telegram.ext import CommandHandler
from telegram.ext import filters
from telegram.ext import MessageHandler
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import Application

from commands.getgigs import get_gigs
from commands.nolastfm import nolastfm
from commands.nonewevents import nonewevents
from commands.details import details
from commands.start import start
from interactions.conn_lfm_conversation import conn_lfm_conversation
from interactions.disconn_lfm_conversation import disconn_lfm_conversation

logger = logging.getLogger('A.loa')
logger.setLevel(logging.DEBUG)


def load_interactions(application: Application) -> None:
    """
    Loads all command handlers on start.
    Args: application: application for adding handlers to
    """
    load_conversations(application)
    load_commands(application)
    load_messages(application)
    load_error(application)
    return None


def load_conversations(application: Application) -> None:
    """
    Loads all conversation handlers on start.
    Args: application: application for adding handlers to.
    """
    application.add_handler(conn_lfm_conversation())
    application.add_handler(disconn_lfm_conversation())
    return None


def load_commands(application: Application) -> None:
    """
    Loads all command handlers on start.
    Args: application: application for adding handlers to.
    """
    application.add_handler(CommandHandler('getgigs', get_gigs))
    application.add_handler(CommandHandler('nolastfm', nolastfm))
    application.add_handler(CommandHandler('nonewevents', nonewevents))
    application.add_handler(CommandHandler('start', start))
    return None


def load_messages(application: Application) -> None:
    """
    Loads all message handlers on start.
    Args: application: application for adding handlers to.
    """
    application.add_handler(MessageHandler(
        filters.Regex('/([0-9]{2,3})$'), details))
    return None


def load_error(application: Application):
    """
    Loads error handler message handlers on start.
    Args: application: application for adding handler to
    """
    def error_handle(update: Update, context: CallbackContext) -> None:
        """
        Determine what to do when update causes error.
        """
        logger.warning(f'Update {update} caused error {context.error}')
        return None

    application.add_error_handler(error_handle)
    return None