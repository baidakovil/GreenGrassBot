import os
import logging
from typing import List, Tuple, Dict, Union
from datetime import datetime
from dataclasses import asdict
from contextlib import contextmanager

from telegram import Update
import sqlite3
from sqlite3 import IntegrityError, OperationalError

from config import Cfg
from interactions.utils import timestamp_to_text
from services.custom_classes import ArtScrobble, Event, User, UserSettings

logger = logging.getLogger('A.db')
logger.setLevel(logging.DEBUG)

CFG = Cfg()


@contextmanager
def get_connection(db_path: str, params: Dict = None, case: str = None) -> None:
    """
    Context manager for proper executing sqlite connections.
    Args: 
        db_path: path to database
        params: optional, parameters to execute query with, for error output (at debugging)
        case: optional, parameter to split error cases
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = 1")
        yield conn
        conn.commit()
    except IntegrityError as E:
        logger.info(f'CATCHED IntegrityError: {E}, params: {params}')
    except OperationalError as E:
        logger.info(f'CATCHED OperationalError: {E}, params: {params}')
    except Exception as E:
        logger.warning(f'CATCHED SomeError: {E}')
    finally:
        conn.close()
        return None


class Db:
    """
    Class for working with sqlite3 database.
    """

    def __init__(self, initial: bool = False) -> None:
        """
        Provide db file creating if it was not found or db recreating if needed.
        Args: 
            initial: should be supplied only once in main().
                If True, then basing on value of DELETE_DB_ATSTART parameter
                database will be rewritten from scratch or not.
        """
        self.db_path = os.path.join(CFG.PATH_DBFILES, CFG.FILE_DB)
        self.script_path = os.path.join(CFG.PATH_DBFILES, CFG.FILE_DB_SCRIPT)
        if initial and CFG.DELETE_DB_ATSTART:
            os.remove(self.db_path)
            logger.info(f'DB DELETED from: {self.db_path}')
            self.create_db()
            return None
        elif not os.path.isfile(self.db_path):
            logger.info(f'DB not found in file: {self.db_path}')
            self.create_db()
            return None

    def create_db(self) -> None:
        """
        Creates db and logging number of created tables in it.
        """
        os.makedirs(CFG.PATH_DBFILES, exist_ok=True)
        with get_connection(self.db_path) as con:
            cursor = con.cursor()
            with open(self.script_path, 'r') as f:
                script = f.read()
            cursor.executescript(script)
            logger.info(f'Forward script executed')
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND tbl_name != "sqlite_sequence"
                """)
            tbl_num = cursor.fetchone()
            logger.info(f'{tbl_num[0]} tables created')
            return None

    def _execute_query(
            self, query: str, case: str = None, params: Dict = None,
            select: bool = False, selectone: bool = True,
            getaffected: bool = False) -> Union[None, str, int]:
        """
        Execute queries to db.
        Args:
            query: single query to execute
            case: optional, parameter for context manager to split error cases
            params: parameters to execute query with
            select: True if query should return a value OR values
            selectone: True if query should return only one row
            getaffected: True if query should return quantity of affected rows.
        Note, getaffected should not combined with selects.
        """
        answer = None
        with get_connection(self.db_path, params, case) as con:
            cursor = con.cursor()
            cursor.execute(query, params)
            if select and selectone:
                answer = cursor.fetchone()
            elif select:
                answer = cursor.fetchall()
            elif getaffected:
                answer = cursor.rowcount
            cursor.close()
            return answer

    #################################
    ###### WRITES/WRITE-READS #######
    #################################

    async def save_user(self, update: Update) -> None:
        """
        Saves to DB:
            Tg user info, without replacement (according wsql_users() query);
            Default user settings without replacement (initial=True).
        Args: update: standart PTB argument for bot update.
        """
        user = User(
            user_id=update.message.from_user.id,
            username=update.message.from_user.username,
            first_name=update.message.from_user.first_name,
            last_name=update.message.from_user.last_name,
            language_code=update.message.from_user.language_code,
        )
        await self.wsql_users(user)
        await self.wsql_settings(update.message.from_user.id, initial=True)
        return None

    async def wsql_users(self, user: User) -> None:
        """
        Write all fields to table 'users'
        """
        query = """
        INSERT INTO users (user_id, username, first_name, last_name, language_code)
        VALUES (:user_id, :username, :first_name, :last_name, :language_code);
        """
        params = asdict(user)['reg_datetime'] = timestamp_to_text(
            datetime.now())
        params = asdict(user)
        self._execute_query(
            query=query,
            params=params,
            case='wsql_users'
        )
        logger.info(
            f"User with username: {user.username} and user_id: {user.user_id} added")

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
        affected = self._execute_query(
            query=query,
            params=params,
            getaffected=True
        )
        return affected

    async def wsql_settings(self,
                            user_id,
                            min_listens: int = CFG.DEFAULT_MIN_LISTENS,
                            notice_day: int = CFG.DEFAULT_NOTICE_DAY,
                            notice_time: str = CFG.DEFAULT_NOTICE_TIME,
                            nonewevents: int = 1,
                            initial=False,
                            ) -> None:
        """
        write all fields to _usersettings row where UserSettings.user_id = user_id
        """
        uset = UserSettings(
            user_id,
            min_listens,
            notice_day,
            notice_time,
            nonewevents,
        )
        if initial:
            query = """
            INSERT INTO usersettings (user_id, min_listens, notice_day, notice_time, nonewevents)
            VALUES (:user_id, :min_listens, :notice_day, :notice_time, :nonewevents);
            """
        else:
            query = """
            INSERT OR REPLACE INTO usersettings (user_id, min_listens, notice_day, notice_time, nonewevents)
            VALUES (:user_id, :min_listens, :notice_day, :notice_time, :nonewevents);
            """
        affected = self._execute_query(
            query=query,
            params=asdict(uset),
            getaffected=True
        )
        if initial:
            logger.info(
                f"User with user_id: {user_id} insert initial settings: {affected} rows affected")
        else:
            logger.info(
                f"User with user_id: {user_id} updated settings: {affected} rows affected")
        return affected

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

    async def rsql_settings(self, user_id: int) -> UserSettings:
        """
        Return current usersettings.
        """
        query = """
        SELECT * FROM usersettings
        WHERE user_id = ?
        """
        record = self._execute_query(query, params=(
            user_id,), select=True, selectone=False)[0]
        print(record)
        result = [record[i] for i in range(len(record))]
        print(result)
        usersettings = UserSettings(
            user_id=result[0],
            min_listens=result[1],
            notice_day=result[2],
            notice_time=result[3],
            nonewevents=result[4],
        )
        return usersettings

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

    async def rsql_finalquestion(self, user_id, art_name) -> bool:
        """
        Answers should this art_name be sent to user at this day (date=today always?)
        """
        params = {'user_id': user_id,
                  'art_name': art_name,
                  'delay': CFG.DAYS_MIN_DELAY_ARTCHECK,
                  'period': CFG.DAYS_PERIOD_MINLISTENS, }
        query = """
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

    #################################
    ############ DELETES ############
    #################################

    async def dsql_useraccs(self, user_id, lfm) -> None:
        """
        Delete lfm account.
        """
        query = """
        DELETE FROM useraccs
        WHERE user_id = ? AND lfm = ?
        """
        affected = self._execute_query(
            query, params=(user_id, lfm), getaffected=True)
        return affected
