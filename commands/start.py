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
"""This file, like other in /commands, contains callback funcs for same name command."""

import logging

from telegram import Update
from telegram.ext import CallbackContext

from config import Cfg
from db.db_service import Db
from services.message_service import alarm_char, i34g, reply, send_message, up_full

db = Db()
CFG = Cfg()

logger = logging.getLogger('A.sta')
logger.setLevel(logging.DEBUG)


async def start(update: Update, context: CallbackContext) -> None:
    """
    Callback function. Sends start message. Alarms developer. If user have accounts,
    list it.
    Args:
        update, context: standart PTB callback signature
    """
    user_id, _, _, username = up_full(update)
    await db.save_user(update)
    locale = await db.rsql_locale(user_id=user_id)
    if locale is None:
        logger.warning('Can not read locale settings. It should not be like this!')
        locale = CFG.LOCALE_DEFAULT
    if CFG.NEW_USER_ALARMING:
        await send_message(
            context, CFG.DEVELOPER_CHAT_ID, text=f'New user: {user_id}, {username}'
        )
    lfm_accs = await db.rsql_lfmuser(user_id)
    if not lfm_accs:
        pretext = await i34g('start.user', locale=locale)
    else:
        lfm_accs = ['_' + alarm_char(acc) + '_' for acc in lfm_accs]
        pretext = await i34g(
            'start.hacker',
            accs_noalarm=', '.join(lfm_accs),
            locale=locale,
        )
    message = await i34g('start.message', locale=locale, qty=CFG.MAX_LFM_ACCOUNT_QTY)
    commands = await build_commands_description(locale)
    copyright = await i34g('start.copyright', locale=locale)
    text = pretext + message + commands + copyright
    await reply(update, text)
    return None


async def build_commands_description(locale: str) -> str:
    """
    Build localized text with command descriptions in groups for show to user at /start.
    Args:
        locale: locale to use
    Returns:
        string with description
    """
    desc = []
    commands_dict = CFG.COMMANDS_ALL
    for group, coms in commands_dict.items():
        desc.append('\n\n')
        desc.append(await i34g(f'commands_groups.{group}', locale=locale))
        for com in coms:
            desc.append('\n')
            command_desc = await i34g(f'commands.{com}_full', locale=locale)
            desc.append(f'*/{com}* — {command_desc}')
    desc = ''.join(desc)
    return desc
