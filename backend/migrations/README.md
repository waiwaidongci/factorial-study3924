# Schema 版本说明

## v2（当前）
本地启动由SQLAlchemy metadata创建初始表。自然键为邮箱、试验code、(study,temperature,glaze)、**(study,specimen_code,measure_no)**、运行名、提案标题。测量与alpha使用DOUBLE。

`trial_readings` 在 v1 基础上增加 `measure_no INT NOT NULL DEFAULT 1`，同一独立试片可登记多个仪器测次；应用层先按试片对各测次取算术均值，分析样本按独立试片计。

v1 → v2 在 MySQL 8.0 手动执行 `002_repeat_measures.sql`（幂等，可重复运行）：
1. 缺列时 `ALTER TABLE trial_readings ADD COLUMN measure_no INT NOT NULL DEFAULT 1`；
2. 按索引列定位并删除 v1 的 `(study_id,specimen_code)` 唯一约束（不依赖具体约束名）；
3. 建立 `uq_reading_study_specimen_measure (study_id,specimen_code,measure_no)`。

历史 `factor_runs.result`（v1 指纹与残差结构）和已获批 `followup_plans` 不做数据迁移，应用对缺失字段全部容错。

## v1
自然键为邮箱、试验code、(study,temperature,glaze)、(study,specimen_code)、运行名、提案标题。后续升级需版本化DDL，当前未提供生产迁移工具。
