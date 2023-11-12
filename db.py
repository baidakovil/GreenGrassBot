import os
import logging
from pathlib import Path
from typing import List, Union, Tuple
from datetime import datetime, date
from collections import namedtuple
from dataclasses import dataclass
from dataclasses import asdict
import sqlite3
from sqlite3 import IntegrityError, OperationalError

from config import Cfg

logger = logging.getLogger('A.E')
logger.setLevel(logging.DEBUG)

CFG = Cfg()


def timestamp_to_text(timestamp):
    f = '%Y-%m-%d %H:%M:%S'
    return timestamp.strftime(f)


def date_to_text(date):
    f = '%Y-%m-%d'
    return date.strftime(f)


@dataclass
class ArtScrobble:
    """
    Class for keeping user scrobble for 1 artist
    """
    user_id: int
    art_name: str
    scrobble_date: str
    lfm: str
    scrobble_count: int


@dataclass
class Event:
    """
    Class for keeping one event and lineup
    """
    event_date: str
    place: str
    locality: str
    country: str
    event_source: str
    link: str
    lineup: List[int]


@dataclass
class User:
    """
    Class for keeping user info
    """
    user_id: int
    username: str
    first_name: str
    last_name: str
    language_code: str
    accs: List[str] = None
    reg_datetime: str = None


@dataclass
class UserSettings:
    """
    Class for keeping user settings
    """
    user_id: int
    min_listens: int = CFG.DEFAULT_MIN_LISTENS
    notice_day: int = CFG.DEFAULT_NOTICE_DAY
    notice_time: str = CFG.DEFAULT_NOTICE_TIME


BOT_FOLDER = os.path.dirname(os.path.realpath(__file__))


class Db:
    """Db works here"""

    def __init__(self, dbpath, dbname, script_pathname, hard_rewrite=False):
        self.dbpath = dbpath
        self.dbname = dbname
        self.hard_rewrite = hard_rewrite
        self.script_pathname = script_pathname
        self._conn = self.connection()
        logger.info(
            f'DB connected to: {os.path.join(BOT_FOLDER, self.dbpath, self.dbname)}')

    def create_db(self):
        Path(os.path.join(BOT_FOLDER, self.dbpath)).mkdir(
            parents=True, exist_ok=True)
        connection = sqlite3.connect(os.path.join(
            BOT_FOLDER, self.dbpath, self.dbname))
        connection.execute("PRAGMA foreign_keys = 1")
        cursor = connection.cursor()
        with open(os.path.join(BOT_FOLDER, self.script_pathname), 'r') as f:
            script = f.read()
            cursor.executescript(script)
        connection.commit()
        logger.info(f'Forward script executed')
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND tbl_name != "sqlite_sequence"
            """)
        tbl_num = cursor.fetchone()
        logger.info(f'{tbl_num[0]} tables created')
        cursor.close()
        connection.close()

    def connection(self):
        db_path = os.path.join(BOT_FOLDER, self.dbpath, self.dbname)
        if not os.path.isfile(db_path):
            logger.info(f'DB not found in file: {db_path}')
            self.create_db()
        elif self.hard_rewrite:
            os.remove(db_path)
            logger.info(f'Db DELETED FROM: {db_path}')
            self.create_db()
        connection = sqlite3.connect(db_path)
        connection.execute("PRAGMA foreign_keys = 1")
        return connection

    def _execute_query(self, query, params=None, select=False, selectone=True):
        cursor = self._conn.cursor()
        cursor.execute(query, params)
        if select and selectone:
            records = cursor.fetchone()
            cursor.close()
            return records
        elif select:
            records = cursor.fetchall()
            cursor.close()
            return records
        else:
            self._conn.commit()
        cursor.close()

    #################################
    ###### WRITES/WRITE-READS #######
    #################################

    def error_handler(f):
        async def wrapper(*args, **kwargs):
            try:
                return await f(*args, **kwargs)
            except IntegrityError as E:
                if 'UNIQUE constraint failed: useraccs.user_id, useraccs.lfm' in E.args[0]:
                    logger.warning(
                        f'{f.__name__}| EXCEPTION CASE№2.1.1: {E}, args: {args}, kwargs: {kwargs}')
                    return 'Sorry, you already have this account'
                    # CASE№2.1.1 try to insert non-unique
                elif 'UNIQUE constraint failed' in E.args[0]:
                    logger.warning(
                        f'{f.__name__}|EXCEPTION CASE№2.1.2: {E}, args: {args}, kwargs: {kwargs}')
                    return 'NOTUNIQUE'
                    # CASE№2.1.2 try to insert non-unique
                elif 'NOT NULL constraint failed: useraccs.user_id' in E.args[0]:
                    logger.warning(
                        f'{f.__name__}|EXCEPTION CASE№2.1.3: {E}, args: {args}, kwargs: {kwargs}')
                    return f'Sorry, max {CFG.MAX_LFM_ACCOUNT_QTY} accounts possible'
                    # CASE№2.1.3 no slots for lfm accs
                else:
                    logger.warning(
                        f'{f.__name__}|Unknown error: {E}, args: {args}, kwargs: {kwargs}')
            except OperationalError as E:
                if 'database is locked' in E.args[0]:
                    logger.warning(
                        f'{f.__name__}|EXCEPTION CASE№2.2: {E}, args: {args}, kwargs: {kwargs}')
                    # CASE№2.2 another program use database
                elif 'row value misused' in E.args[0]:
                    logger.warning(
                        f'{f.__name__}|EXCEPTION CASE№2.3: {E}, args: {args}, kwargs: {kwargs}')
                    # CASE№2.3 stumbled when parentnesses were but they dont needed
                else:
                    logger.warning(
                        f'{f.__name__}|EXCEPTION CASE№2.10: {E}, args: {args}, kwargs: {kwargs}')
                    # CASE№2.10
            except Exception as E:
                logger.warning(f'{f.__name__}|EXCEPTION CASE№2.99: {E}')
                # CASE№2.99 unknown exception for me
        return wrapper

    @error_handler
    async def wsql_users(self, user: User) -> None:
        """
        Write all fields to table 'users'
        """
        query = """
        INSERT INTO users (user_id, username, first_name, last_name, language_code)
        VALUES (:user_id, :username, :first_name, :last_name, :language_code);
        """
        self._execute_query(
            query=query,
            params=asdict(user),
        )
        logger.info(
            f"User with username: {user.username} and user_id: {user.user_id} added")

    @error_handler
    async def wsql_useraccs(self, user_id, lfm) -> None:
        """
        Add account to 'useraccs' if there is free slots and if it's unique
        """
        params = {'user_id': user_id, 'lfm': lfm,
                  'max_qty': CFG.MAX_LFM_ACCOUNT_QTY}
        query = """
        INSERT INTO useraccs (user_id, lfm)
        VALUES (
            (SELECT :user_id WHERE 
                (SELECT COUNT(*) FROM useraccs 
                WHERE user_id = :user_id) <= :max_qty-1),
            :lfm
            );
        """
        self._execute_query(
            query=query,
            params=params,
        )

        logger.info(f"User with user_id: {user_id} added lfm account: {lfm}")
        return f'Account {lfm} added'

    @error_handler
    async def wsql_settings(self,
                            user_id,
                            min_listens: int = CFG.DEFAULT_MIN_LISTENS,
                            notice_day: int = CFG.DEFAULT_NOTICE_DAY,
                            notice_time: str = CFG.DEFAULT_NOTICE_TIME,
                            ) -> None:
        """
        write all fields to _usersettings row where UserSettings.user_id = user_id
        """
        uset = UserSettings(
            user_id,
            min_listens,
            notice_day,
            notice_time,
        )
        query = """
        INSERT OR REPLACE INTO usersettings (user_id, min_listens, notice_day, notice_time)
        VALUES (:user_id, :min_listens, :notice_day, :notice_time);
        """
        self._execute_query(
            query=query,
            params=asdict(uset),
        )
        logger.info(f"User with user_id: {user_id} updated settings")

    @error_handler
    async def wsql_scrobbles(self, ars: ArtScrobble) -> None:
        """
        write all fields to _scrobbles row
        """
        query = """
        INSERT OR REPLACE INTO scrobbles (user_id, lfm, art_name, scrobble_date, lfm, scrobble_count)
        VALUES (:user_id, :lfm, :art_name, :scrobble_date, :lfm, :scrobble_count);
        """
        self._execute_query(
            query=query,
            params=asdict(ars),
        )
        # logger.info(f"Added scrobble for user_id: {ars.user_id}, art_name: {ars.art_name}")

    @error_handler
    async def wsql_events_lups(self, eventList: List[Event]) -> None:
        """
        write one row to _events. 
        If OK, 
        write n rows to _lineups (n=count(art_names)) 
        """
        query_ev = """
        INSERT INTO events (event_date, place, locality, country, event_source, link)
        SELECT :event_date, :place, :locality, :country, :event_source, :link
        WHERE NOT EXISTS(
            SELECT 1 from events WHERE event_date=:event_date AND place=:place AND locality=:locality
            );
        """
        query_lup = """
            INSERT OR IGNORE INTO lineups (event_id, art_name)
            VALUES ((SELECT event_id FROM events WHERE event_date=? AND place=? AND locality=?), ?)
            """

        for ev in eventList:
            self._execute_query(
                query=query_ev,
                params=asdict(ev),
            )
            for art_name in ev.lineup:
                self._execute_query(
                    query=query_lup,
                    params=(ev.event_date, ev.place, ev.locality, art_name),
                )
            logger.debug(
                f"Added event with event_date:{ev.event_date}, event_place:{ev.place}")
        logger.info(f'All events for added')

    @error_handler
    async def wsql_artcheck(self, art_name: str) -> None:
        """
        write that art_name was checked
        """
        query = """
            INSERT OR REPLACE INTO artnames(art_name, check_datetime)
            VALUES (?, datetime("now"));
            """
        self._execute_query(
            query=query,
            params=(art_name,),
        )
        logger.info(f"Added or updated artcheck: {art_name}")

    @error_handler
    async def wsql_artcheck_test(self, art_name: str) -> None:
        """
        write that art_name was checked
        """
        query = """
            INSERT OR REPLACE INTO artnames(art_name, check_datetime)
            VALUES (?, "2023-11-09 13:00:00");
            """
        self._execute_query(
            query=query,
            params=(art_name,),
        )
        logger.info(f"Added or updated artcheck_test: {art_name}")

    @error_handler
    async def wsql_sentarts(self, user_id, art_name) -> None:
        """
        write all fields to _sentarts
        """
        params = {
            'user_id': user_id,
            'art_name': art_name,
            'delay': CFG.DAYS_MIN_DELAY_ARTCHECK,
            'period': CFG.DAYS_PERIOD_MINLISTENS,
        }
        query = """
        INSERT INTO sentarts (user_id, sent_datetime, art_name, event_id)
        SELECT :user_id AS user_id,
                DATETIME("now") AS sent_datetime,
                art_name, 
                events.event_id
                FROM lineups JOIN events
                ON lineups.event_id = events.event_id 
                WHERE
                    lineups.art_name = :art_name
                    AND
                    events.event_date >= DATE("now")
                    AND
                    events.event_id NOT IN 
                        (SELECT event_id FROM sentarts WHERE user_id= :user_id AND art_name= :art_name)
                    AND
                    :art_name IN
                        (SELECT art_name FROM scrobbles
                        WHERE JULIANDAY("now")-JULIANDAY(scrobble_date) <= :period
                        GROUP BY user_id, art_name
                        HAVING 
                        SUM(scrobble_count) >= (SELECT min_listens FROM usersettings WHERE user_id= :user_id)
                        AND
                        user_id= :user_id);
        """
        self._execute_query(
            query=query,
            params=params,
        )
        logger.info(f"Added sentarts for user_id: {user_id}")

    @error_handler
    async def wsql_lastarts(self, user_id, shorthand, art_name) -> None:
        """
        write all fields to _lastarts
        """
        query = """
        INSERT INTO lastarts (user_id, shorthand, art_name, shorthand_date)
        VALUES (?,?,?,date("now"));
        """
        self._execute_query(
            query=query,
            params=(user_id, shorthand, art_name)
        )
        logger.info(f"Added lastarts for user_id: {user_id}")

    #################################
    ########### READS ###############
    #################################

    async def rsql_numtables(self) -> int:
        """
        Returns quantity of tables in DB.
        """
        query = """
        SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND tbl_name != "sqlite_sequence"
        """
        tbl_num = self._execute_query(
            query,
            select=True,
        )
        return tbl_num[0]

    @error_handler
    async def rsql_maxshorthand(self, user_id) -> int:
        """
        Returns maximum number of shorthand-quick link for user,
        or zero if there is no shorthands.
        """
        query = """
        SELECT IFNULL((SELECT MAX(shorthand) FROM lastarts WHERE user_id = ?), 0)
        """
        record = self._execute_query(query, params=(user_id,), select=True)
        return record[0]

    @error_handler
    async def rsql_lfmuser(self, user_id: int) -> List[str]:
        """
        return list of lastfm users for user
        """
        query = f"""
        SELECT lfm FROM useraccs
        WHERE user_id = ?
        """
        record = self._execute_query(query, params=(
            user_id,), select=True, selectone=False)
        result = [record[i][0] for i in range(len(record))]
        logger.debug(f'Return lastfm users for user_id {user_id}: {result}')
        return result

    @error_handler
    async def rsql_artcheck(self,
                            user_id,
                            art_name) -> datetime:
        """
        Answers should this artist be checked for events. Returns 0 if not, 1 if should.
        Conditions for answer "1":
        a) no checked for concerts yet OR checked far ago
        b) user had listen this artist much enough
        """
        params = {
            'user_id': user_id,
            'art_name': art_name,
            'delay': CFG.DAYS_MIN_DELAY_ARTCHECK,
            'period': CFG.DAYS_PERIOD_MINLISTENS,
        }
        query = f"""
        SELECT 
            CASE 
                WHEN
                    ((SELECT check_datetime FROM artnames WHERE art_name = :art_name) IS NULL
                        OR
                    (SELECT JULIANDAY(DATETIME("NOW")) - JULIANDAY(check_datetime) FROM artnames
                    WHERE art_name = :art_name) > :delay)
                AND (:art_name IN (SELECT art_name FROM scrobbles
                    WHERE JULIANDAY("now")-JULIANDAY(scrobble_date) <= :period
                    GROUP BY user_id, art_name
                    HAVING
                        SUM(scrobble_count) >= (SELECT min_listens FROM usersettings WHERE user_id= :user_id)
                            AND
                        user_id= :user_id))
                THEN 1
                ELSE 0
        END;
        """
        record = self._execute_query(query, params=params, select=True)
        return record[0]

    @error_handler
    async def rsql_getallevents(self, user_id: int, shorthand: int) -> List[Tuple]:
        """
        Return all events as answer on user's shortcut pressing.
        Conditions to select events:
        a) art_name same as in Tg message near shortcut
        b) event_date after the date when Tg message was sent.
        """
        params = {'user_id': user_id, 'shorthand': shorthand}
        query = f"""
        SELECT
        (SELECT art_name FROM lastarts WHERE shorthand= :shorthand) as artist, 
        event_date, place, locality, country, link FROM events WHERE
        event_id IN 
            (SELECT event_id FROM lineups 
            WHERE art_name= (SELECT art_name FROM lastarts WHERE shorthand= :shorthand))
        AND event_date >= (SELECT shorthand_date FROM lastarts WHERE shorthand= :shorthand)
        ORDER BY event_date
        """
        ev = self._execute_query(query, params=params,
                                 select=True, selectone=False)
        logger.info(f'User {user_id} requests shorthand {shorthand}')
        return ev

    @error_handler
    async def rsql_finalquestion(self, user_id, art_name) -> bool:
        """
        Answers should this art_name be sent to user at this day (date=today always?)
        """
        params = {'user_id': user_id,
                  'art_name': art_name,
                  'delay': CFG.DAYS_MIN_DELAY_ARTCHECK,
                  'period': CFG.DAYS_PERIOD_MINLISTENS, }
        query = f"""
        SELECT 
            CASE
                WHEN
                    (SELECT COUNT(*) FROM lineups
                    JOIN events
                    ON lineups.event_id = events.event_id 
                    WHERE
                        lineups.art_name = :art_name
                        AND
                        events.event_date >= DATE("now")
                        AND
                        events.event_id NOT IN 
                            (SELECT event_id FROM sentarts WHERE user_id= :user_id AND art_name= :art_name)
                        AND
                        :art_name IN
                            (SELECT art_name FROM scrobbles
                            WHERE JULIANDAY("now")-JULIANDAY(scrobble_date) <= :period
                            GROUP BY user_id, art_name
                            HAVING 
                            SUM(scrobble_count) >= (SELECT min_listens FROM usersettings WHERE user_id= :user_id)
                            AND
                            user_id= :user_id))
                THEN 1
		        ELSE 0
	        END
        """
        record = self._execute_query(query, params=params, select=True)
        return bool(record[0])
