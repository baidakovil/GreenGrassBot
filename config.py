import logging

logger = logging.getLogger('A.CFG')
logger.setLevel(logging.DEBUG)


class Cfg:
    """
    Class for keeping bot configuration.
    """

    def __init__(self) -> None:
        # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # # # # # # #   USER  # # INTER # FACE  # # # # # # # #
        # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # maximum number for quick link to event. after this it will reset zero
        self.INTEGER_MAX_SHORTHAND = 99

        # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # # # # # # USER  # # DEFAULT # # SETTINGS  # # # # # #
        # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # How many time user should listen in last week to be notified
        self.DEFAULT_MIN_LISTENS = 2

        # Day to send news about events. -1 is every day (?)
        self.DEFAULT_NOTICE_DAY = -1

        # Default UTC time to send news
        self.DEFAULT_NOTICE_TIME = '12:30:00'

        # Default UTC time to send news
        self.DEFAULT_NONEWEVENTS: int = 0

        # Default UTC time to send news
        self.DEFAULT_LOCALE = 'en'

        # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # # # # # # # # #   BOT   # #   LOGIC   # # # # # # # #
        # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # possible quantity of accounts at last.fm to keep
        self.MAX_LFM_ACCOUNT_QTY = 3

        # days quantity to load scrobbles for new user. Whithout SQL OVER(), like now,
        # only DAYS_INITIAL_TIMEDELAY <= DAYS_PERIOD_MINLISTENS make sense
        self.DAYS_INITIAL_TIMEDELAY = 4

        # minimum delay to update info about artist's events
        self.DAYS_MIN_DELAY_ARTCHECK = 2

        # how many days consider for min_listens users's config, i.e. it is y in [x
        # scrobbles in y days] condition, where x is DEFAULT_MIN_LISTENS
        self.DAYS_PERIOD_MINLISTENS = 4

        # settings for APScheduler when set daily jobs
        self.CRON_JOB_KWARGS = {'misfire_grace_time': 3600 * 12, 'coalesce': True}

        # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # # # # # # # # # # #   LOGGER  # # # # # # # # # # # #
        # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # Path to logger files
        self.PATH_LOGGER = '.'

        # Filename for rotating logger (logging all runs)
        self.FILE_ROTATING_LOGGER = 'logger.log'

        # Max filesize for rotating logger
        self.BYTES_MAX_ROTATING_LOGGER = 1024 * 1024 * 20

        # Quantity of files, keeping by rotating logger
        self.QTY_BACKUPS_ROTATING_LOGGER = 5

        # Developer contacts to inform about errors or new users
        self.DEVELOPER_CHAT_ID = 144297913

        # Whether bot should inform about new users
        self.NEW_USER_ALARMING = False

        # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # # # # # # # # #   DATA  #  BASE # # # # # # # # # # #
        # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # if True, will create new DB every run
        self.DELETE_DB_ATSTART = False

        # Path to database AND creating script
        self.PATH_DBFILES = 'db'

        # Path to db file
        self.FILE_DB = 'ggb_sqlite.db'

        # Filename of db-creating script
        self.FILE_DB_SCRIPT = 'ggb_sqlite.sql'

        # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # # # # # # # # # # #   PARSER  # # # # # # # # # # # #
        # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # delay between lastfm apis requests
        self.SECONDS_SLEEP_XMLLOAD = 1

        # delay between lastfm events loads in scraper
        self.SECONDS_SLEEP_HTMLLOAD = 1

        # how many scrobbles will be on single XML request, max 200
        self.QTY_SCROBBLES_XML = 200
