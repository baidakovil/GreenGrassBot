import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger('A.CFG')
logger.setLevel(logging.DEBUG)
load_dotenv('.env')


class Cfg():
    def __init__(self, test=os.getenv('TEST') == 'true'):
        if test:
            logger.info(f'Cfg Class says: TEST CONFIG LOADING')
            # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # # # # # # BOT  # # # CONFIG # # # # # # # # # # # # #
            # # # # # # # # # # # # # # # # # # # # # # # # # # # #

            self.SECONDS_SLEEP_JSONLOAD = 1                 #  delay between lastfm apis requests
            self.SECONDS_SLEEP_HTMLLOAD = 1                 #  delay between lastfm events loads in scraper
            self.INTEGER_MAX_SHORTHAND = 99                 #  maximum number for quick link to event
            self.MAX_LFM_ACCOUNT_QTY = 3                    #  possible quantity of accounts at last.fm to keep
            self.DAYS_INITIAL_TIMEDELAY = 2                 #  days quantity to load scrobbles for new user
            self.DAYS_MIN_DELAY_ARTCHECK = 1                #  minimum delay to update info about artist's events
            self.DAYS_PERIOD_MINLISTENS = 7                 #  how many days consider for minListens users's config
                                                            #  (i.e. it is y in [x scrobbles in y days] condition, where x is DEFAULT_MIN_LISTENS)

            self.PATH_LOGGER = 'log'                        #  Path to logger files
            self.FILE_SESSION_LOGGER = 'logger.log'         #  Filename for session logger (logging only last run)
            self.FILE_ROTATING_LOGGER = 'logger.log'        #  Filename for rotating logger (logging all runs)
            self.BYTES_MAX_ROTATING_LOGGER = 1024*1024*20   #  Max filesize for rotating logger
            self.QTY_BACKUPS_ROTATING_LOGGER = 5            #  Quantity of files, keeping by rotating logger
            
            self.PATH_DBFILES = 'db'                        #  Path to database AND creating script
            self.FILE_DB = 'ggb_sqlite.db'                  #  Path to db file
            self.FILE_DB_SCRIPT = 'create_db.sql'           #  Filename of db-creating script

            # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # # # # # # USER  # # # DEFAULT # # # # # # # # # # # #
            # # # # # # # # # # # # # # # # # # # # # # # # # # # #

            self.DEFAULT_MIN_LISTENS = 5                    #  How many time user should listen in last week to be notified
            self.DEFAULT_NOTICE_DAY = -1                    #  Day to send news about events. -1 is every day (?)
            self.DEFAULT_NOTICE_TIME = '12:00:00'           #  Default UTC time to send news.
    