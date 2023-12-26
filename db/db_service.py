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
"""This file contains class Db and logic related to sqlite database."""

import logging
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from sqlite3 import IntegrityError, OperationalError
from typing import Any, Iterator, List, Literal, Optional, Tuple, Union

from telegram import Update

import config as cfg
from services.custom_classes import ArtScrobble, BotUser, Event, UserSettings
from services.logger import logger
from services.timeconv_service import timestamp_to_text

logger = logging.getLogger(name='A.db')
logger.setLevel(logging.DEBUG)


@contextmanager
def get_connection(db_path: str, params: Any = None) -> Iterator[sqlite3.Connection]:
    """
    Context manager for proper executing sqlite queries.
    Args:
        db_path: path to database
        params: optional, parameters to execute query with, for error
        output (at debugging)
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = 1")
        yield conn
        conn.commit()
    except IntegrityError as e:
        logger.info('CATCHED IntegrityError: %s, params: %s', e, params)
    except OperationalError as e:
        logger.info('CATCHED OperationalError: %s, params: %s', e, params)
    finally:
        conn.close()


def create_db(db) -> None:
    """
    Creates db and log number of created tables for control/debug.
    """
    os.makedirs(cfg.PATH_DBFILES, exist_ok=True)
    with get_connection(db.db_path) as con:
        cursor = con.cursor()
        with open(db.script_path, 'r', encoding='utf-8') as f:
            script = f.read()
        cursor.executescript(script)
        logger.info('Forward script executed')
        cursor.execute(
            """
            SELECT COUNT(*) FROM sqlite_master 
            WHERE type="table" AND tbl_name != "sqlite_sequence"
            """
        )
        tbl_num = cursor.fetchone()
        logger.info('%s tables created', tbl_num[0])
        return None


def execute_query(
    db,
    query: str,
    params: Any = None,
    mode: Literal['execute', 'selectone', 'selectmany', 'getaffected'] = 'execute',
) -> Union[Any, List[Any], int, None]:
    """
    Execute queries to db. Note, getaffected arg should not be combined with
    selects.
    Args:
        db: database Db()
        query: single query to execute
        params: parameters to execute query with
        mode:
            execute: if query should not return anything (for consistency)
            select: if query should return a value OR values
            selectone: if query should return only one row
            getaffected: if query should return quantity of affected rows
    """
    answer = None
    with get_connection(db.db_path, params) as con:
        cursor = con.cursor()
        cursor.execute(query, params)
        if mode == 'selectone':
            answer = cursor.fetchone()
        elif mode == 'selectmany':
            answer = cursor.fetchall()
        elif mode == 'getaffected':
            answer = cursor.rowcount
        cursor.close()
        return answer


def affected_hard_check(affected: Union[Any, List[Any], int, None]) -> int:
    """
    Provide hard check of "affected" var. Good for linter and for DB control.
    Args:
        affected: value returned by _executed_query
    """
    if isinstance(affected, int) and affected >= 0:
        return affected
    raise TypeError("Affected rows quantity returns non-int! DB fails")


def tuple_hard_check(record: Union[Any, List[Any], int, None]) -> tuple:
    """
    Provide hard check of db output. Good for linter and for DB control.
    Args:
        record: value returned by _executed_query
    """
    if isinstance(record, tuple):
        return record
    raise TypeError("execute_query() returns not tuple! DB fails")


def list_hard_check(record: Union[Any, List[Any], int, None]) -> list:
    """
    Provide hard check of db output. Good for linter and for DB control.
    Args:
        record: value returned by _executed_query
    """
    if isinstance(record, list):
        return record
    raise TypeError("execute_query() returns not list! DB fails")


class Db:
    """
    Class for working with sqlite3 database. Convention for function names is to use
    proper first name symbol(s): r - read, w - write, wr/rw - write and read, d - delete
    data. After that symbol(s) "sql_" and then function name
    """

    def __init__(self, initial: bool = False) -> None:
        """
        Provide db file creating if it was not found or db recreating if needed.
        Args:
            initial: should be supplied only once in main(). If True, then basing on
            value of DELETE_DB_ATSTART parameter database will be rewritten from scratch
            or not.
        """
        self.db_path = os.path.join(cfg.PATH_DBFILES, cfg.FILE_DB)
        self.script_path = os.path.join(cfg.PATH_DBFILES, cfg.FILE_DB_SCRIPT)
        if initial and cfg.DELETE_DB_ATSTART:
            os.remove(self.db_path)
            logger.info('DB DELETED from: %s', self.db_path)
            create_db(self)
            return None

        if not os.path.isfile(self.db_path):
            logger.info('DB not found in file: %s', self.db_path)
            create_db(self)
        return None

    #################################
    ###### WRITES/WRITE-READS #######
    #################################

    async def save_user(self, update: Update) -> None:
        """
        Saves to DB: a) Tg user info, without replacement (according wsql_users()
        query); b) Default user settings, if there is no default settings saved.
        Args:
            update: object representing incoming update (message)
        """
        assert update.message
        assert update.message.from_user
        username = update.message.from_user.username
        lastname = update.message.from_user.last_name
        language_code = update.message.from_user.language_code
        user_tg_locale = language_code if language_code else cfg.LOCALE_DEFAULT

        user = BotUser(
            user_id=update.message.from_user.id,
            username=username if username else '',
            first_name=update.message.from_user.first_name,
            last_name=lastname if lastname else '',
            language_code=user_tg_locale,
        )

        await self.wsql_users(user)
        await self.wsql_settings(
            user_id=update.message.from_user.id, user_tg_locale=user_tg_locale
        )

    async def wsql_users(self, user: BotUser) -> None:
        """
        Write all fields to table 'users' if it was not saved for this user_id
        Agrs:
            user: user to save.
        """
        query = """
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, language_code)
        VALUES (:user_id, :username, :first_name, :last_name, :language_code);
        """
        params = asdict(user)
        params['reg_datetime'] = timestamp_to_text(datetime.now())
        execute_query(self, query=query, params=params, mode='execute')
        logger.info(
            "BotUser with username: %s and user_id: %s added",
            user.username,
            user.user_id,
        )
        return None

    async def wsql_useraccs(self, user_id: int, lfm: str) -> int:
        """
        Add account to 'useraccs' if there is free slots and if it's unique. Slots and
        uniqueness checked for second time there (first time in callback function).
        Args:
            user_id: Tg user_id field lfm: last.fm account name to save
        Returns:
            affected rows quantity
        """
        params = {
            'user_id': user_id,
            'lfm': lfm,
            'max_qty': cfg.MAX_LFM_ACCOUNT_QTY,
        }
        query = """
        INSERT INTO useraccs (user_id, lfm)
        VALUES (
            (SELECT :user_id WHERE 
                (SELECT COUNT(*) FROM useraccs 
                WHERE user_id = :user_id) <= :max_qty-1),
            :lfm);
        """
        affected = execute_query(self, query=query, params=params, mode='getaffected')
        return affected_hard_check(affected)

    async def wsql_settings(self, **kw) -> int:
        """
        Saves default user settings. Args:
            user_id, min_listens, notice_day, nonewevents, locale: see desription in
            custom_classes.py
        Returns:
            affected rows quantity
        # TODO checking for keywords are possible keywords
        """

        #  Get dict with defaul settings as 'template'.
        user_id = kw['user_id']
        user_tg_locale = kw.get('user_tg_locale', cfg.LOCALE_DEFAULT)
        def_sett = asdict(UserSettings(user_id=user_id, locale=user_tg_locale))
        #  Get dict with current settings, if exists
        cur_sett = await self.rsql_settings(user_id=user_id)
        wrt_sett = cur_sett.__dict__ if cur_sett is not None else def_sett
        #  Replace current or default with given
        use_vals = {
            key: kw[key] if key in kw else wrt_sett[key] for key in wrt_sett.keys()
        }

        query = """
        INSERT OR REPLACE 
        INTO usersettings (user_id, min_listens, notice_day, notice_time, nonewevents, locale)
        VALUES (:user_id, :min_listens, :notice_day, :notice_time, :nonewevents, :locale);
        """

        affected = execute_query(self, query=query, params=use_vals, mode='getaffected')

        if affected:
            logger.debug('Settings changed')
        else:
            logger.warning("Settings was not changed to")

        return affected_hard_check(affected)

    async def wsql_scrobbles(self, ars: ArtScrobble) -> None:
        """
        Write single artist scrobble info. This used to determine whether user should be
        notified about thist artist.
        Args:
            ars: GGB scrobble object
        """
        query = """
        INSERT OR REPLACE 
        INTO scrobbles (user_id, lfm, art_name, scrobble_date, lfm, scrobble_count)
        VALUES (:user_id, :lfm, :art_name, :scrobble_date, :lfm, :scrobble_count);
        """
        execute_query(self, query=query, params=asdict(ars), mode='execute')
        logger.debug(
            "Added scrobble for user_id: %s, art_name: %s", ars.user_id, ars.art_name
        )
        return None

    async def wsql_events_lups(self, event_list: List[Event]) -> None:
        """
        Write list of event-rows to event table AND list of lists of art-rows to lineup
        table.
        """
        query_ev = """
        INSERT INTO events (event_date, place, locality, country, event_source, link)
        SELECT :event_date, :place, :locality, :country, :event_source, :link
        WHERE NOT EXISTS(
            SELECT 1 from events WHERE event_date=:event_date AND place=:place AND locality=:locality);
        """
        query_lup = """
            INSERT OR IGNORE INTO lineups (event_id, art_name)
            VALUES ((SELECT event_id FROM events WHERE event_date=? AND place=? AND locality=?), ?)
            """
        count_lup = 0
        count_ev = 0
        for ev in event_list:
            execute_query(self, query=query_ev, params=asdict(ev))
            for art_name in ev.lineup:
                execute_query(
                    self,
                    query=query_lup,
                    params=(ev.event_date, ev.place, ev.locality, art_name),
                    mode='execute',
                )
                logger.debug(
                    "Added lineup with art_name: %s, event_date: %s, event_place: %s",
                    art_name,
                    ev.event_date,
                    ev.place,
                )
                count_lup += 1
            logger.debug(
                "Added event event_date: %s, event_place: %s", ev.event_date, ev.place
            )
            count_ev += 1
        logger.info('Added to db: %s events, %s line-ups', count_ev, count_lup)
        return None

    async def wsql_jobs(self, user_id: int, chat_id: int) -> None:
        """
        Writes info for new daily job, i.e. which chat to send daily news to.
        Args:
            user_id: Tg user_id field
            chat_id: Tg chat_id field
        """
        query = """
            INSERT OR IGNORE INTO jobs (user_id, chat_id) 
            VALUES (?, ?)
            """
        affected = execute_query(
            self, query=query, params=(chat_id, user_id), mode='getaffected'
        )
        if affected:
            logger.info("Added job in DB: user_id %s, chat_id %s", user_id, chat_id)
        else:
            logger.info("Not added job in DB: user_id %s, chat_id %s", user_id, chat_id)
        return None

    async def wsql_artcheck(self, art_name: str) -> None:
        """
        Writes or updates info about art_name checking time, for escaping multiple
        checking. Time delay controlled by cfg.DAYS_MIN_DELAY_ARTCHECK.
        Args:
            art_name: artist name that was checked
        """
        query = """
            UPDATE artnames SET check_datetime = datetime("now") 
            WHERE art_name = ?
            """
        execute_query(self, query=query, params=(art_name,), mode='execute')
        logger.debug("Added or updated artcheck: %s", art_name)
        return None

    async def wsql_last_sent_arts(
        self, user_id: int, shorthand: int, art_name: str
    ) -> None:
        """
        Write all fields to lastarts table. It used to access detailed event info with
        'shortcuts' like: /01 Beatles /02 Sebastian Bach. THEN write all fields to sentarts
        table. It used to escape multiple send of same events to same user.
        Args:
            user_id: Tg user_id field
            shorthand: integer shorthand number, max to cfg.INTEGER_MAX_SHORTHAND
            art_name: corresponding artist name
        """
        query_lastarts = """
        INSERT INTO lastarts (user_id, shorthand, art_name, shorthand_date)
        VALUES (?,?,?,date("now"));
        """
        execute_query(
            self,
            query=query_lastarts,
            params=(user_id, shorthand, art_name),
            mode='execute',
        )
        logger.debug("Added lastarts for user_id: %s", user_id)

        params = {
            'user_id': user_id,
            'art_name': art_name,
            'delay': cfg.DAYS_MIN_DELAY_ARTCHECK,
            'period': cfg.DAYS_PERIOD_MINLISTENS,
        }
        query_sentarts = """
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
        execute_query(self, query=query_sentarts, params=params, mode='execute')
        logger.debug("Added sentarts for user_id: %s", user_id)

        return None

    #################################
    ########### READS ###############
    #################################

    async def rsql_users(self, user_id: int) -> int:
        """
        Returns 0 or 1 as quantity of user_id in users table.
        """
        query = """
        SELECT COUNT(*) FROM users WHERE user_id=?
        """
        record = execute_query(
            self,
            query,
            params=(user_id,),
            mode='selectone',
        )
        record = tuple_hard_check(record)[0]
        return record

    def rsql_jobs(self) -> List[Tuple]:
        """
        NOT_ASYNC!
        Returns full job list bot have.
        Returns:
            List of tuples in format (user_id, chat_id) or empty list
        """
        query = """
        SELECT user_id, chat_id FROM jobs
        """
        records = execute_query(self, query, params=(), mode='selectmany')
        records = list_hard_check(records)
        if records == []:
            logger.debug('No jobs in db')
        else:
            logger.debug('Returned jobs: %s jobs', len(records))
        return records

    async def rsql_locale(self, user_id: int) -> Union[str, None]:
        """
        Returns user locale setting.
        Args:
            user_id: Tg user_id field
        Returns:
            string with written setting or None if settings was not found.
        """
        query = """
        SELECT locale FROM usersettings
        WHERE user_id = ?
        """
        record = execute_query(self, query, params=(user_id,), mode='selectone')
        if record is None:
            logger.debug('Return empty locale settings for user_id %s', user_id)
            return record
        record = tuple_hard_check(record)[0]
        return record

    async def rsql_settings(self, user_id: int) -> Optional[UserSettings]:
        """
        Returns user settings.
        #TODO rewrite ro row_factory with dict access to fields.
        Args:
            user_id: Tg user_id field
        Returns:
            BotUserSetting dataclass object or False if settings was not found.
        """
        query = """
        SELECT * FROM usersettings
        WHERE user_id = ?
        """
        record = execute_query(self, query, params=(user_id,), mode='selectone')
        if record is None:
            logger.debug('Return empty settings for user_id %s', user_id)
            return record
        record = tuple_hard_check(record)
        usersettings = UserSettings(
            user_id=record[0],
            min_listens=record[1],
            notice_day=record[2],
            notice_time=record[3],
            nonewevents=int(record[4]),
            locale=record[5],
        )
        logger.debug('Return settings for user_id %s: OK', user_id)
        return usersettings

    async def rsql_maxshorthand(self, user_id: int) -> int:
        """
        Returns maximum number of shorthand-quick link for user, or zero if there is no
        shorthands.
        Args:
            user_id: Tg user_id field
        Returns:
            maximum integer in shorthand field of lastarts table
        """
        query = """
        SELECT IFNULL((SELECT MAX(shorthand) FROM lastarts WHERE user_id = ?), 0)
        """
        record = execute_query(self, query, params=(user_id,), mode='selectone')
        record = tuple_hard_check(record)[0]
        logger.debug('Return maxshorthand for user_id %s: %s', user_id, record)
        return record

    async def rsql_lfmuser(self, user_id: int) -> List[str]:
        """
        Returns list of lastfm accounts for user.
        Args:
            user_id: Tg user_id field
        Returns:
            list with account names
        """
        query = """
        SELECT lfm FROM useraccs
        WHERE user_id = ?
        """
        record = execute_query(self, query, params=(user_id,), mode='selectmany')
        record = list_hard_check(record)
        result = [record[i][0] for i in range(len(record))]
        logger.debug('Return lastfm users for user_id %s: %s', user_id, result)
        return result

    async def rsql_artcheck(self, user_id: int, art_name: str) -> int:
        """
        Answers should this artist be checked for events. Returns 0 or 1. Conditions for
        "1": a) no checked for concerts yet OR checked far before
        DAYS_MIN_DELAY_ARTCHECK b) user had listen this artist much enough, i.e. not
        less than min_listens times in last DAYS_PERIOD_MINLISTENS days.
        Args:
            user_id: Tg user_id field
            art_name: artist_name
        Returns:
            0 or 1.
        """
        params = {
            'user_id': user_id,
            'art_name': art_name,
            'delay': cfg.DAYS_MIN_DELAY_ARTCHECK,
            'period': cfg.DAYS_PERIOD_MINLISTENS,
        }
        query = """
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
        record = execute_query(self, query, params=params, mode='selectone')
        record = tuple_hard_check(record)[0]
        return record

    async def rsql_getallevents(self, user_id: int, shorthand: int) -> List[Tuple]:
        """
        Return all events as answer on user's quick-link shortcut pressing. Conditions
        to select events: a) art_name same as in Tg message near shortcut b) event_date
        after the date when Tg message was sent.
        Args:
            user_id: Tg user_id field
            shorthand: integer shortcut
        Returns:
            List of tuples with field artist name and 5 other fields from events
            table

        """
        params = {'user_id': user_id, 'shorthand': shorthand}
        query = """
        SELECT
        (SELECT art_name FROM lastarts WHERE shorthand= :shorthand AND user_id= :user_id) as artist, 
        event_date, place, locality, country, link FROM events WHERE
        event_id IN 
            (SELECT event_id FROM lineups 
            WHERE art_name= (SELECT art_name FROM lastarts WHERE shorthand= :shorthand AND user_id= :user_id))
        AND event_date >= (SELECT shorthand_date FROM lastarts WHERE shorthand= :shorthand AND user_id= :user_id)
        ORDER BY event_date
        """
        ev = execute_query(self, query, params=params, mode='selectmany')
        ev = list_hard_check(ev)
        logger.info('BotUser %s requests shorthand %s', user_id, shorthand)
        return ev

    async def rsql_lastdayscrobble(self, user_id: int, lfm: str) -> Union[str, None]:
        """
        Returns last scrobble_date value for user_id-lfm pair. Used to decide how old
        scrobble to load and avoid excess API using.
        Args:
            user_Id: Tg user_id field
            lfm: last.fm user name
        Returns: string in f_sql_date format (timeconv_service.py)
        """
        query = """
        SELECT MAX(scrobble_date) FROM scrobbles
        WHERE user_id = ? AND lfm = ?
        """
        record = execute_query(self, query, params=(user_id, lfm), mode='selectone')

        if record is None:
            logger.debug('No last scrobbles found for %s', user_id)
            return record

        logger.debug('BotUser %s requests last scrobble date', user_id)
        record = tuple_hard_check(record)[0]
        return record

    async def rsql_finalquestion(self, user_id: int, art_name: str) -> int:
        """
        Answers, should this art_name be sent to user. Conditions to answer "1": a)
        event was not sent before, b) in last DAYS_PERIOD_MINLISTENS user have no less X
        listens, where X is min_listens user setting, c) event date is in future, d)
        artist name present in lineups table.
        Args:
            user_id: Tg user_id field
            art_name: artist name to answer.
        Returns:
            0 or 1.
        """
        params = {
            'user_id': user_id,
            'art_name': art_name,
            'delay': cfg.DAYS_MIN_DELAY_ARTCHECK,
            'period': cfg.DAYS_PERIOD_MINLISTENS,
        }
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
        record = execute_query(self, query, params=params, mode='selectone')
        record = tuple_hard_check(record)[0]
        return record

        #################################
        ############ DELETES ############
        #################################


async def dsql_useraccs(db, user_id, lfm) -> Tuple[int, int]:
    """
    Delete lfm account and relational to lfm account data.
    Args:
        db: database Db()
        user_id: Tg user_id field
        lfm: last.fm account name to delete
    Returns:
        tuple with quantities of affected rows in scrobbles/useraccs tables
    """
    query_del_sa = """
    DELETE FROM sentarts
    WHERE user_id = ? AND (art_name IN (SELECT art_name FROM scrobbles
    WHERE user_id = ? AND lfm = ?));
    """
    query_del_la = """
    DELETE FROM lastarts
    WHERE user_id = ? AND (art_name IN (SELECT art_name FROM scrobbles
    WHERE user_id = ? AND lfm = ?));
    """
    query_del_scr = """
    DELETE FROM scrobbles
    WHERE user_id = ? AND lfm = ?
    """
    query_del_ua = """
    DELETE FROM useraccs
    WHERE user_id = ? AND lfm = ?
    """
    execute_query(db, query_del_sa, params=(user_id, user_id, lfm))

    execute_query(db, query_del_la, params=(user_id, user_id, lfm))

    affected_scr = execute_query(
        db, query_del_scr, params=(user_id, lfm), mode='getaffected'
    )

    affected_ua = execute_query(
        db, query_del_ua, params=(user_id, lfm), mode='getaffected'
    )

    return (affected_hard_check(affected_scr), affected_hard_check(affected_ua))


async def dsql_user(db, user_id) -> bool:
    """
    Delete all the user info.
    Args:
        db: database Db()
        user_id: Tg user_id field
    Returns:
        True if user deleted normally, False if some useraccs or user_ids was not
        deleted
    """
    logger.info('BotUser %s request account deleting', user_id)
    problem = None
    useraccs = await db.rsql_lfmuser(user_id)

    for lfm in useraccs:
        _, affected_ua = await dsql_useraccs(db, user_id=user_id, lfm=lfm)
        if not affected_ua:
            problem = True
            logger.info('Problem when deleting lfm for %s', user_id)

    query_del_user = """
    DELETE FROM users WHERE user_id = ?
    """

    affected_users = execute_query(
        db, query_del_user, params=(user_id,), mode='getaffected'
    )
    if not affected_users:
        problem = True
        logger.info('Problem when deleting user_id for %s', user_id)
    else:
        logger.info('BotUser %s deleted all the info', user_id)
    return problem is None
