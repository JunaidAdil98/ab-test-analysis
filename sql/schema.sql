-- =====================================================================
-- schema.sql  —  Experiment event table (MySQL 8)
-- Load: schema.sql -> LOAD DATA the CSV -> analysis_queries.sql
-- =====================================================================

DROP TABLE IF EXISTS `experiment`;

CREATE TABLE `experiment` (
  `user_id`    VARCHAR(16)   NOT NULL,
  `variant`    ENUM('control','treatment') NOT NULL,
  `device`     ENUM('mobile','desktop')    NOT NULL,
  `user_type`  ENUM('new','returning')     NOT NULL,
  `visit_date` DATE          NOT NULL,
  `converted`  TINYINT       NOT NULL,
  `revenue`    DECIMAL(10,2) NOT NULL DEFAULT 0,
  PRIMARY KEY (`user_id`),
  KEY `ix_variant` (`variant`),
  KEY `ix_device`  (`device`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Example load (adjust path / secure_file_priv as needed):
-- LOAD DATA INFILE '/path/experiment.csv'
-- INTO TABLE `experiment`
-- FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
-- LINES TERMINATED BY '\n' IGNORE 1 ROWS
-- (user_id, variant, device, user_type, visit_date, converted, revenue);
