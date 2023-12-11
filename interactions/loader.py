# Green Grass Bot — Ties the music you're listening to with the concert it's playing at.
# Copyright (C) 2021-2023 Ilia Baidakov <baidakovil@gmail.com>

# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <https://www.gnu.org/licenses/>.
"""This file contains load_interactions(), which is called when bot starting."""

import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from commands.details import details
from commands.getgigs import getgigs
from commands.help import help_call
from commands.nonewevents import nonewevents
from commands.start import start
from commands.warranty import warranty
from interactions.common_handlers import error_handler, unknown_handler
from interactions.conn_lfm_conversation import conn_lfm_conversation
from interactions.delete_user_conversation import delete_user_conversation
from interactions.disconn_lfm_conversation import disconn_lfm_conversation
from interactions.locale_conversation import locale_conversation
from services.logger import logger

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
    application.add_handler(
        MessageHandler(filters.COMMAND, unknown_handler, block=False)
    )


def load_conversations(application: Application) -> None:
    """
    Loads all conversation handlers on start.
    Args: application: application for adding handlers to.
    """
    application.add_handler(conn_lfm_conversation())
    application.add_handler(delete_user_conversation())
    application.add_handler(disconn_lfm_conversation())
    application.add_handler(locale_conversation())


def load_commands(application: Application) -> None:
    """
    Loads all command handlers on start.
    Args: application: application for adding handlers to.
    """
    application.add_handler(CommandHandler('getgigs', getgigs, block=False))
    application.add_handler(CommandHandler('help', help_call, block=False))
    application.add_handler(CommandHandler('nonewevents', nonewevents, block=False))
    application.add_handler(CommandHandler('start', start, block=False))
    application.add_handler(CommandHandler('warranty', warranty, block=False))


def load_messages(application: Application) -> None:
    """
    Loads all message handlers on start.
    Args: application: application for adding handlers to.
    """
    application.add_handler(
        MessageHandler(filters.Regex('/([0-9]{2,3})$'), details, block=False)
    )


def load_error(application: Application):
    """
    Loads error handler message handlers on start.
    Args: application: application for adding handler to
    """
    application.add_error_handler(error_handler)
