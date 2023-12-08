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
"""This file contains config constants. It and '.env' is the only config storages."""

import logging

from dotenv import load_dotenv

load_dotenv('.env')

logger = logging.getLogger('A.cfg')
logger.setLevel(logging.DEBUG)


# # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # #   USER  # # INTER # FACE  # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # #

#  Maximum number for quick link to event. Reaching this, resets to zero.
INTEGER_MAX_SHORTHAND = 99

#  Commands appearing at /start command, i.e. all commands that user should know
COMMANDS_ALL = {
    'concerts': ['getgigs'],
    'manage_accounts': ['connect', 'disconnect', 'delete'],
    'preferences': ['locale', 'nonewevents'],
    'helping_commands': ['start', 'help'],
}

#  Commands from COMMANDS_ALL that should NOT be displayed at Menu button.
COMMANDS_UNDISPLAYED = ['delete', 'nonewevents']

# # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # USER  # # DEFAULT # # SETTINGS  # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # #

#  How many time user should listen the artist in last week to be notified
#  about it's concert.
DEFAULT_MIN_LISTENS = 3

#  Day to send news about events. Not using at the time.
DEFAULT_NOTICE_DAY = -1

#  Default UTC time to send news.
DEFAULT_NOTICE_TIME = '11:48:00'

#  Default setting to show 'There is no new events' message. 0 mean not to show.
DEFAULT_NONEWEVENTS: int = 0

# # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # #   BOT   # #   LOGIC   # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # #

#  Max time to wait for a response from Telegram’s server.
SEC_READ_TIMEOUT = 30

#  Max time to wait for a write operation to complete.
SEC_WRITE_TIMEOUT = 30

#  Possible quantity of accounts at last.fm to keep.
MAX_LFM_ACCOUNT_QTY = 3

#  Days quantity to load scrobbles for new user. Whithout SQL OVER(), like now,
#  only DAYS_INITIAL_TIMEDELAY <= DAYS_PERIOD_MINLISTENS make sense.
DAYS_INITIAL_TIMEDELAY = 4

#  Minimum delay to update info about artist's events.
DAYS_MIN_DELAY_ARTCHECK = 2

#  How many days consider for min_listens users's config, i.e. it is y in [x
#  scrobbles in y days] condition, where x is DEFAULT_MIN_LISTENS.
DAYS_PERIOD_MINLISTENS = 4

# Settings for APScheduler when set daily jobs.
CRON_JOB_KWARGS = {'misfire_grace_time': 3600 * 12, 'coalesce': True}

# # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # #   LOGGER  # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # #

#  Path to logger files.
PATH_LOGGER = '.'

#  Filename for rotating logger (logging all runs).
FILE_ROTATING_LOGGER = 'logger.log'

#  Max filesize for rotating logger.
BYTES_MAX_ROTATING_LOGGER = 1024 * 1024 * 20

#  Quantity of files, keeping by rotating logger.
QTY_BACKUPS_ROTATING_LOGGER = 5

#  Developer contacts to inform about errors or new users.
DEVELOPER_CHAT_ID = 144297913

#  Whether bot should inform about new users.
NEW_USER_ALARMING = True

# # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # #   DATA  #  BASE # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # #

#  If True, will create new DB every run.
DELETE_DB_ATSTART = False

#  Path to database AND creating script.
PATH_DBFILES = 'db'

#  Path to db file.
FILE_DB = 'ggb_sqlite.db'

#  Filename of db-creating script.
FILE_DB_SCRIPT = 'ggb_sqlite.sql'

# # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # #   PARSER  # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # #

#  Delay between lastfm apis requests.
SECONDS_SLEEP_XMLLOAD = 2

#  Delay between lastfm events loads in scraper.
SECONDS_SLEEP_HTMLLOAD = 2

#  How many scrobbles will be on single XML request, max 200.
QTY_SCROBBLES_XML = 200

#  How many concurrent connections (job executions) allowed for /getgigs commnd.
MAX_CONCURRENT_CONN_ATREQUEST = 1

#  How many concurrent connections (job executions) allowed for /getgigs_job.
MAX_CONCURRENT_CONN_ATJOB = 1

# # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # #   TRANSLATIONS  # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # #

#  Locale codes of present translations
LOCALES_ISO = ['en', 'ru', 'uk']

#  Default locale.
LOCALE_DEFAULT = 'en'

#  Locale to store technical strings (API adresses, URLs).
LOCALE_TECHNICAL_STORE = 'en'

#  Translation path.
PATH_TRANSLATIONS = './assets/lang'

#  Filename format for i18n.
FILENAME_FORMAT_I18N = '{locale}.{format}'

#  Set up multilingual bot descriptions at startup
NEED_DESCRIPTION = False

#  Set up multinlingual bot descriptions at startup
NEED_COMMANDS = False
