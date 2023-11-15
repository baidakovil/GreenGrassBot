BEGIN;

-- -----------------------------------------------------
-- Table `artnames`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `artnames` (
  `art_name` NVARCHAR(45) PRIMARY KEY,
  `check_datetime` DATETIME NULL);

-- -----------------------------------------------------
-- Table `events`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `events` (
  `event_id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `event_date` DATE NULL,
  `place` NVARCHAR(255) NULL,
  `locality` NVARCHAR(255) NULL,
  `country` NVARCHAR(255) NULL,
  `event_source` NVARCHAR(45) NOT NULL,
  `link` NVARCHAR(2047) NULL);

-- -----------------------------------------------------
-- Table `lastarts`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `lastarts` (
  `user_id` BIGINT UNSIGNED NOT NULL,
  `shorthand` SMALLINT NOT NULL,
  `art_name` NVARCHAR(45) NULL,
  `shorthand_date` DATE NOT NULL,
  PRIMARY KEY (`user_id`, `shorthand`),
  CONSTRAINT `fk_lastarts_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_lastarts_artnames`
    FOREIGN KEY (`art_name`)
    REFERENCES `artnames` (`art_name`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

-- -----------------------------------------------------
-- Table `lineups`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `lineups` (
  `event_id` INT UNSIGNED NOT NULL,
  `art_name` NVARCHAR(45) NOT NULL,
  PRIMARY KEY (`event_id`, `art_name`),
  CONSTRAINT `fk_lineups_events`
    FOREIGN KEY (`event_id`)
    REFERENCES `events` (`event_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lineups_artnames`
    FOREIGN KEY (`art_name`)
    REFERENCES `artnames` (`art_name`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE TRIGGER insert_uninserted_artists_lineups
  BEFORE INSERT ON lineups
  WHEN NEW.art_name NOT IN (SELECT art_name FROM artnames)
BEGIN
INSERT INTO artnames (art_name) VALUES (NEW.art_name);
END;

-- -----------------------------------------------------
-- Table `scrobbles`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `scrobbles` (
  `user_id` BIGINT UNSIGNED NOT NULL,
  `art_name` NVARCHAR(45) NOT NULL,
  `scrobble_date` DATE NOT NULL,
  `lfm` NVARCHAR(45) NULL,
  `scrobble_count` SMALLINT NULL,
  PRIMARY KEY (`user_id`, `art_name`, `scrobble_date`, `lfm`),
  CONSTRAINT `fk_scrobbles_useraccs`
    FOREIGN KEY (`user_id`, `lfm`)
    REFERENCES `useraccs` (`user_id`, `lfm`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_scrobbles_artnames`
    FOREIGN KEY (`art_name`)
    REFERENCES `artnames` (`art_name`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

CREATE TRIGGER insert_uninserted_artists_scrobbles
  BEFORE INSERT ON scrobbles
  WHEN NEW.art_name NOT IN (SELECT art_name FROM artnames)
BEGIN
INSERT INTO artnames (art_name) VALUES (NEW.art_name);
END;

-- -----------------------------------------------------
-- Table `sentarts`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `sentarts` (
  `user_id` BIGINT UNSIGNED NOT NULL,
  `event_id` INT UNSIGNED NULL,
  `art_name` NVARCHAR(45) NOT NULL,
  `sent_datetime` DATETIME NULL,
  PRIMARY KEY (`user_id`, `event_id`, `art_name`),
  CONSTRAINT `fk_sentarts_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_sentarts_artnames`
    FOREIGN KEY (`art_name`)
    REFERENCES `artnames` (`art_name`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

-- -----------------------------------------------------
-- Table `useraccs`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `useraccs` (
  `user_id` BIGINT UNSIGNED NOT NULL,
  `lfm` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`user_id`, `lfm`),
  CONSTRAINT `fk_useraccs_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`user_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE);

-- -----------------------------------------------------
-- Table `users`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `users` (
  `user_id` BIGINT UNSIGNED NOT NULL,
  `username` NVARCHAR(255) NULL,
  `first_name` NVARCHAR(255) NULL,
  `last_name` NVARCHAR(255) NULL,
  `language_code` NVARCHAR(45) NULL,
  `reg_datetime` DATETIME NULL,
  PRIMARY KEY (`user_id`));

-- -----------------------------------------------------
-- Table `usersettings`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `usersettings` (
  `user_id` BIGINT UNSIGNED NOT NULL,
  `min_listens` TINYINT UNSIGNED NULL,
  `notice_day` SMALLINT NULL,
  `notice_time` TIME NULL,
  `nonewevents` TINYINT NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `fk_usersettings_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);
    
 COMMIT;
