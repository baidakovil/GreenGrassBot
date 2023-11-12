import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger('A.CFG')
logger.setLevel(logging.DEBUG)
BOT_FOLDER = os.path.dirname(os.path.realpath(__file__))
load_dotenv(os.path.join(BOT_FOLDER, '.env'))


class Cfg():
    def __init__(self, test=os.getenv('TEST') == 'true'):
        if test:
            logger.info(f'Cfg Class says: TEST CONFIG LOADING')
            # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # # # # # # BOT  # # # CONFIG # # # # # # # # # # # # #
            # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            self.MAX_LFM_ACCOUNT_QTY = 3            #  possible quantity of accounts at last.fm to keep
            self.DAYS_INITIAL_TIMEDELAY = 2         #  days quantity to load scrobbles for new user
            self.DAYS_MIN_DELAY_ARTCHECK = 1        #  minimum delay to update info about artist's events
            self.DAYS_PERIOD_MINLISTENS = 7         #  how many days consider for minListens users's config
                                                    #  (i.e. it is y in [x scrobbles in y days] condition, where x is minLinstens)
            self.SECONDS_SLEEP_JSONLOAD = 1         #  delay between lastfm apis requests
            self.SECONDS_SLEEP_HTMLLOAD = 1         #  delay between lastfm events loads in scraper
            self.INTEGER_MAX_SHORTHAND = 99         #  maximum number for quick link to event
            # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            # # # # # # USER  # # # DEFAULT # # # # # # # # # # # #
            # # # # # # # # # # # # # # # # # # # # # # # # # # # #
            self.DEFAULT_MIN_LISTENS = 5            #  How many time user should listen in last week to be notified
            self.DEFAULT_NOTICE_DAY = -1            #  Day to send news about events. -1 is every day (?)
            self.DEFAULT_NOTICE_TIME = '12:00:00'   #  Default UTC time to send news.