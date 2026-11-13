-- Schema v2: 支持同一试片的多个仪器复测测次
-- 适用 MySQL 8.0；在 factorial 库手动执行，整脚本幂等可重复运行。
-- 执行前请备份；执行后应用后端新代码（旧代码不知道新列但仍可读取旧行）。

-- 1) 新增测次号列；旧读数全部视为第 1 测次
SET @ddl := (
  SELECT IF(
    (SELECT COUNT(*) FROM information_schema.COLUMNS
       WHERE TABLE_SCHEMA = DATABASE()
         AND TABLE_NAME = 'trial_readings'
         AND COLUMN_NAME = 'measure_no') = 0,
    'ALTER TABLE trial_readings ADD COLUMN measure_no INT NOT NULL DEFAULT 1 AFTER specimen_code',
    'SELECT 1')
);
PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2) 删除 v1 自然键 (study_id, specimen_code)
-- SQLAlchemy 对未命名 UniqueConstraint 的默认名只取首列（uq_trial_readings_study_id），
-- 这里按索引实际包含的列动态定位，不依赖具体约束名。
SELECT INDEX_NAME INTO @old_uq
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'trial_readings'
  AND NON_UNIQUE = 0
  AND INDEX_NAME <> 'PRIMARY'
GROUP BY INDEX_NAME
HAVING GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) = 'study_id,specimen_code'
LIMIT 1;
SET @ddl := IF(@old_uq IS NULL,
               'SELECT 1',
               CONCAT('ALTER TABLE trial_readings DROP INDEX `', @old_uq, '`'));
PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 3) 建立 v2 自然键 (study_id, specimen_code, measure_no)
SET @ddl := (
  SELECT IF(
    (SELECT COUNT(*) FROM information_schema.STATISTICS
       WHERE TABLE_SCHEMA = DATABASE()
         AND TABLE_NAME = 'trial_readings'
         AND INDEX_NAME = 'uq_reading_study_specimen_measure') = 0,
    'ALTER TABLE trial_readings ADD CONSTRAINT uq_reading_study_specimen_measure UNIQUE (study_id, specimen_code, measure_no)',
    'SELECT 1')
);
PREPARE stmt FROM @ddl; EXECUTE stmt; DEALLOCATE PREPARE stmt;
