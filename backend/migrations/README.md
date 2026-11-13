# Schema v1
本地启动由SQLAlchemy metadata创建初始表。自然键为邮箱、试验code、(study,temperature,glaze)、(study,specimen_code)、运行名、提案标题。测量与alpha使用DOUBLE。后续升级需版本化DDL，当前未提供生产迁移工具。
