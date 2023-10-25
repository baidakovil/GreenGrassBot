BEGIN;

CREATE TABLE IF NOT EXISTS `artchecks` (
  `art_id` INT UNSIGNED NOT NULL,
  `check_datetime` DATETIME NULL,
  PRIMARY KEY (`art_id`),
  CONSTRAINT `fk_artchecks_artnames`
    FOREIGN KEY (`art_id`)
    REFERENCES `artnames` (`art_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

-- -----------------------------------------------------
-- Table `artnames`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `artnames` (
  `art_id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `art_name` NVARCHAR(45) NULL,
  `default_name` TINYINT(1) NULL);

-- -----------------------------------------------------
-- Table `events`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `events` (
  `event_id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `is_festival` TINYINT(1) NULL,
  `place` NVARCHAR(255) NULL,
  `locality` NVARCHAR(255) NULL,
  `country` NVARCHAR(255) NULL,
  `event_date` DATE NULL,
  `event_source` NVARCHAR(45) NOT NULL,
  `link` NVARCHAR(2047) NULL);

-- -----------------------------------------------------
-- Table `lastevents`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `lastevents` (
  `user_id` BIGINT UNSIGNED NOT NULL,
  `shorthand` NVARCHAR(2) NOT NULL,
  `event_id` INT UNSIGNED NULL,
  PRIMARY KEY (`shorthand`, `user_id`),
  CONSTRAINT `fk_lastevents_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_lastevents_events`
    FOREIGN KEY (`event_id`)
    REFERENCES `events` (`event_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

-- -----------------------------------------------------
-- Table `lineups`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `lineups` (
  `event_id` INT UNSIGNED NOT NULL,
  `art_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`event_id`, `art_id`),
  CONSTRAINT `fk_lineups_events`
    FOREIGN KEY (`event_id`)
    REFERENCES `events` (`event_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lineups_artnames`
    FOREIGN KEY (`art_id`)
    REFERENCES `artnames` (`art_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

-- -----------------------------------------------------
-- Table `scrobbles`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `scrobbles` (
  `user_id` BIGINT UNSIGNED NOT NULL,
  `scrobble_date` DATE NOT NULL,
  `art_id` INT UNSIGNED NOT NULL,
  `count` SMALLINT NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `fk_scrobbles_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_scrobbles_artnames`
    FOREIGN KEY (`art_id`)
    REFERENCES `artnames` (`art_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

-- -----------------------------------------------------
-- Table `sentevents`
-- -----------------------------------------------------

CREATE TABLE IF NOT EXISTS `sentevents` (
  `user_id` BIGINT UNSIGNED NOT NULL,
  `event_id` INT UNSIGNED NULL,
  `sent_datetime` DATETIME NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `fk_sentevents_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_sentevents_events`
    FOREIGN KEY (`event_id`)
    REFERENCES `events` (`event_id`)
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
  PRIMARY KEY (`user_id`),
  CONSTRAINT `fk_usersettings_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);
    
 COMMIT;
