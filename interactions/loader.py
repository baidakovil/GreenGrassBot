import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from commands.details import details
from commands.getgigs import getgigs
from commands.nolastfm import nolastfm
from commands.nonewevents import nonewevents
from commands.start import start
from interactions.common_handlers import error_handle
from interactions.conn_lfm_conversation import conn_lfm_conversation
from interactions.delete_user_conversation import delete_user_conversation
from interactions.disconn_lfm_conversation import disconn_lfm_conversation
from interactions.locale_conversation import locale_conversation

logger = logging.getLogger('A.loa')
logger.setLevel(logging.DEBUG)


def load_interactions(application: Application) -> None:
    """
    Loads all command handlers on start.
    Args: application: application for adding handlers to
    TODO answer when unknown command sent
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
    application.add_handler(delete_user_conversation())
    application.add_handler(disconn_lfm_conversation())
    application.add_handler(locale_conversation())
    return None


def load_commands(application: Application) -> None:
    """
    Loads all command handlers on start.
    Args: application: application for adding handlers to.
    """
    application.add_handler(CommandHandler('getgigs', getgigs))
    application.add_handler(CommandHandler('nolastfm', nolastfm))
    application.add_handler(CommandHandler('nonewevents', nonewevents))
    application.add_handler(CommandHandler('start', start))
    return None


def load_messages(application: Application) -> None:
    """
    Loads all message handlers on start.
    Args: application: application for adding handlers to.
    """
    application.add_handler(MessageHandler(filters.Regex('/([0-9]{2,3})$'), details))
    return None


def load_error(application: Application):
    """
    Loads error handler message handlers on start.
    Args: application: application for adding handler to
    """
    application.add_error_handler(error_handle)
    return None
