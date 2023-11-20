BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "artnames" (
	"art_name"	NVARCHAR(45),
	"check_datetime"	DATETIME,
	PRIMARY KEY("art_name")
);
CREATE TABLE IF NOT EXISTS "events" (
	"event_id"	INTEGER,
	"event_date"	DATE,
	"place"	NVARCHAR(255),
	"locality"	NVARCHAR(255),
	"country"	NVARCHAR(255),
	"event_source"	NVARCHAR(45) NOT NULL,
	"link"	NVARCHAR(2047),
	PRIMARY KEY("event_id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "lastarts" (
	"user_id"	BIGINT UNSIGNED NOT NULL,
	"shorthand"	SMALLINT NOT NULL,
	"art_name"	NVARCHAR(45),
	"shorthand_date"	DATE NOT NULL,
	PRIMARY KEY("user_id","shorthand"),
	CONSTRAINT "fk_lastarts_artnames" FOREIGN KEY("art_name") REFERENCES "artnames"("art_name") ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT "fk_lastarts_users" FOREIGN KEY("user_id") REFERENCES "users"("user_id") ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS "lineups" (
	"event_id"	INT UNSIGNED NOT NULL,
	"art_name"	NVARCHAR(45) NOT NULL,
	CONSTRAINT "fk_lineups_artnames" FOREIGN KEY("art_name") REFERENCES "artnames"("art_name") ON DELETE CASCADE ON UPDATE CASCADE,
	PRIMARY KEY("event_id","art_name"),
	CONSTRAINT "fk_lineups_events" FOREIGN KEY("event_id") REFERENCES "events"("event_id") ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS "scrobbles" (
	"user_id"	BIGINT UNSIGNED NOT NULL,
	"art_name"	NVARCHAR(45) NOT NULL,
	"scrobble_date"	DATE NOT NULL,
	"lfm"	NVARCHAR(45),
	"scrobble_count"	SMALLINT,
	PRIMARY KEY("user_id","art_name","scrobble_date","lfm"),
	CONSTRAINT "fk_scrobbles_artnames" FOREIGN KEY("art_name") REFERENCES "artnames"("art_name") ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT "fk_scrobbles_useraccs" FOREIGN KEY("user_id","lfm") REFERENCES "useraccs"("user_id","lfm") ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS "sentarts" (
	"user_id"	BIGINT UNSIGNED NOT NULL,
	"event_id"	INT UNSIGNED,
	"art_name"	NVARCHAR(45) NOT NULL,
	"sent_datetime"	DATETIME,
	CONSTRAINT "fk_sentarts_artnames" FOREIGN KEY("art_name") REFERENCES "artnames"("art_name") ON DELETE NO ACTION ON UPDATE NO ACTION,
	PRIMARY KEY("user_id","event_id","art_name"),
	CONSTRAINT "fk_sentarts_users" FOREIGN KEY("user_id") REFERENCES "users"("user_id") ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT "fk_sentarts_events" FOREIGN KEY ("event_id") REFERENCES "events" ("event_id") ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS "useraccs" (
	"user_id"	BIGINT UNSIGNED NOT NULL,
	"lfm"	VARCHAR(45) NOT NULL,
	PRIMARY KEY("user_id","lfm"),
	CONSTRAINT "fk_useraccs_users" FOREIGN KEY("user_id") REFERENCES "users"("user_id") ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS "users" (
	"user_id"	BIGINT UNSIGNED NOT NULL,
	"username"	NVARCHAR(255),
	"first_name"	NVARCHAR(255),
	"last_name"	NVARCHAR(255),
	"language_code"	NVARCHAR(45),
	"reg_datetime"	DATETIME,
	PRIMARY KEY("user_id")
);
CREATE TABLE IF NOT EXISTS "usersettings" (
	"user_id"	BIGINT UNSIGNED NOT NULL,
	"min_listens"	TINYINT UNSIGNED,
	"notice_day"	SMALLINT,
	"notice_time"	TIME,
	"nonewevents"	TINYINT,
	"locale"	NVARCHAR(45),
	PRIMARY KEY("user_id"),
	CONSTRAINT "fk_usersettings_users" FOREIGN KEY("user_id") REFERENCES "users"("user_id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TRIGGER insert_uninserted_artists_lineups
  BEFORE UPDATE ON lineups
  WHEN NEW.art_name NOT IN (SELECT art_name FROM artnames)
BEGIN
INSERT INTO artnames (art_name) VALUES (NEW.art_name);
END;

CREATE TRIGGER insert_uninserted_artists_scrobbles
  BEFORE INSERT ON scrobbles
  WHEN NEW.art_name NOT IN (SELECT art_name FROM artnames)
BEGIN
INSERT INTO artnames (art_name) VALUES (NEW.art_name);
END;

COMMIT;
