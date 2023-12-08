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
"""This file contains fn to build error messages for user (debug: use error_handler)."""

from services.message_service import i34g


async def error_text(error_code: int, acc: str, user_id: int) -> str:
    """
    Returns error message for user.
    Args:
        error_code: code returned by urllib lib or any number for convention
        acc: account name raised the error, to make error more pleasible
    """
    error_dict = {
        403: await i34g("news_builders.403", acc=acc, user_id=user_id),
        404: await i34g("news_builders.404", acc=acc, user_id=user_id),
        90: await i34g("news_builders.90", user_id=user_id),
        91: await i34g("news_builders.91", user_id=user_id),
        92: await i34g("news_builders.92", user_id=user_id),
    }
    some_error_text = await i34g(
        "news_builders.some_error", err=error_code, acc=acc, user_id=user_id
    )
    return error_dict.get(error_code, some_error_text)
