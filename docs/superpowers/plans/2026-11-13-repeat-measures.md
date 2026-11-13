# 仪器复测（同片多测次）导入与按独立试片聚合 — 实施计划

日期：2026-11-13
分支建议：`feature/repeat-measures`（当前在 `main`，提交前先开分支）

## 1. 需求拆解（验收口径）

1. 仪器复测表不再因试片重号被整体拒收；CSV 支持可选测次号列 `measure_no`。
2. 同一试片的多个测次**先取均值**，再以该均值作为该独立试片的观测进入 ANOVA；样本数 `n` 按**独立试片数**计，不按读数行数计，杜绝改编号虚增样本。
3. 重复测次去重规则：
   - 同 `(specimen_code, measure_no)` 出现多次且 `strength_mpa` 完全相同 → 视为同一测次的重复登记，**去重保留一条**。
   - 同 `(specimen_code, measure_no)` 出现多次但强度值不同 → 数据冲突，**整份导入拒收**（422，指明试片号与测次号及冲突值）。
   - 同一 `specimen_code` 出现在不同处理格（温度/釉层不一致）→ **整份拒收**（指明试片号与冲突格）。
4. 拒收不留残项：整个导入在一次事务内完成，任何校验失败不写 study/cell/reading 任何一行。
5. 页面可核对：原始读数（含测次号）与聚合依据（每片由哪几个测次、各自原值、算术均值、测次数）都能查看。
6. 分析指纹：指纹输入保留**全部原始读数**（含 `measure_no` 与原值），因此两个试片均值相同但原值分布不同的试验，指纹必然不同；同时算法标签升版本。
7. 兼容旧表：无 `measure_no` 列的旧 CSV 正常导入（默认测次号 1）；旧库、旧 run 结果 JSON、已获批方案不改动、仍可读；旧指纹保持可复现。
8. 行上限改为「原始读数行 ≤ 3000」，平衡/每格 ≥3 的约束作用在**聚合后的独立试片**上。

## 2. 现状与影响面

- 模型 `TrialReading`：唯一键 `(study_id, specimen_code)`，无测次列 → 需加 `measure_no` 并改唯一键为 `(study_id, specimen_code, measure_no)`。
- `schemas/reading.py ReadingInput`：四字段，pydantic 默认忽略额外列 → 加可选 `measure_no`。
- `services/design.py validate_design`：第 10 行直接以「编号集合大小≠行数」拒收重复测量 → 重写为「原始行校验 + 按试片聚合 + 对聚合结果做平衡校验」。
- `services/study_service.create_study`：逐行插 reading → 改为插去重后的原始读数行；校验前置、单事务。
- `services/anova.analyze_factorial`：直接用传入行做分组/SS/残差 → 先聚合再计算；残差按独立试片输出；结果里带聚合摘要。
- `services/run_service.execute_run`：`raw_readings` 给指纹与分析；算法标签 `balanced-fixed-anova-holm-v1` → 指纹快照带 `measure_no` 的全部原始行，标签升 `v2`（旧 JSON 不动）。
- `services/reading_service` / `routes/readings.py`：列表接口增加 `view=raw|aggregated`。
- `services/cell_service`：`n` 改为独立试片数（distinct specimen），均值/标准差基于试片均值；附原始读数计数。
- 前端 `Data.vue`、`samples` store、`api/readings.ts`、`types/domain.ts`、`CellMatrix.vue`、`RunSummary.vue`、`Results.vue`：双视图与聚合依据展示。
- `migrations/README.md` + 新增版本化 DDL 脚本；README 统计口径章节同步。

## 3. 后端设计

### 3.1 数据模型与迁移

`trial_readings` 增加：

```python
measure_no: Mapped[int] = mapped_column(Integer, default=1)
__table_args__ = (UniqueConstraint('study_id','specimen_code','measure_no',
                                   name='uq_reading_study_specimen_measure'),)
```

- 新建库：`Base.metadata.create_all` 直接得到新结构（seed 走同一模型，旧 seed 行不写该列时默认 1，模型层 default 生效）。
- 已有库：新增 `backend/migrations/002_repeat_measures.sql`（幂等，用 `information_schema` 判断列/约束是否存在后再 `ALTER`；先 `DROP INDEX uq_trial_readings_study_id_specimen_code` 再加新唯一键，`ALTER TABLE ... ADD COLUMN measure_no INT NOT NULL DEFAULT 1`）。README 说明手动执行顺序。
- 自然键文档更新为 `(study, specimen_code, measure_no)`，试片业务键仍为 `(study, specimen_code)`。

### 3.2 输入 schema（兼容旧表）

```python
class ReadingInput(BaseModel):
    model_config = ConfigDict(extra='ignore')
    specimen_code: str = Field(min_length=1, max_length=80)
    temperature: str = Field(min_length=1, max_length=40)
    glaze: str = Field(min_length=1, max_length=40)
    strength_mpa: float = Field(gt=0, le=5000, allow_inf_nan=False)
    measure_no: int = Field(default=1, ge=1, le=999)
```

- CSV 无该列 → pydantic 默认 1；空字符串需在 service 层先归一为 1（pydantic 对空串转 int 会报错，故在 `DictReader` 后做 `row.get('measure_no') in (None,'') → '1'` 的预处理）。
- 列名白名单：`specimen_code,temperature,glaze,strength_mpa,measure_no`，出现未知列直接 422（避免拼写错误静默丢列）。

### 3.3 校验与聚合（核心，新 `services/aggregation.py`）

函数 `aggregate_specimens(rows) -> (aggregated_rows, audit)`：

1. 顺序遍历原始行，构造键 `(specimen_code, measure_no)`：
   - 首次出现：登记 `{cell:(temperature,glaze), values:[strength_mpa]}`。
   - 再次出现且值与已登记值完全相等（`==`，DOUBLE 原值比较）：去重，不计新行，审计计数 `duplicate_dropped += 1`。
   - 再次出现但值不等：`ValueError` → 422「测次冲突：试片 X 测次 k 存在不同读数 a/b」。
2. 同时维护 `specimen_code -> (temperature,glaze)`：同片跨行处理格不一致 → 422「试片 X 跨处理格：格1 与 格2」。
3. 按试片分组聚合（算术均值，Python `sum/len` 与 numpy 口径一致，均为双精度求和；均值用 `float(np.mean(...))`）：
   - 聚合行：`{specimen_code, temperature, glaze, strength_mpa: 均值, measure_count: m, raw_values: [...]}`。
4. `validate_design(rows, a_levels, b_levels)` 新流程：
   - 先 `aggregate_specimens`；
   - 对**聚合行**做：因子水平合法、完整交叉、各格独立试片数相等且 ≥3；
   - 有限性对原始行与聚合行都检查；
   - 返回 `n`（每格独立试片数）与聚合审计。
5. `create_study`：先全部校验通过再开写；写入的 reading 为**去重后原始行**（带 `measure_no`），行数上限 3000 作用在去重后行数；任何异常 `db.rollback()`，不残留。

### 3.4 ANOVA 与指纹

- `analyze_factorial(rows, ...)`：入口先聚合（原始行可能带 `measure_no`，也兼容没有该键的旧调用），全部 SS/MSE/df/对比基于**每试片一个均值**的平衡设计；`n = 每格独立试片数`，`df_E = ab(n−1)`。
- 结果新增：
  - `measure_mode`: `single`（全部测次号=1 且每片一行）或 `repeated`；
  - `raw_reading_count`、`specimen_count`、`duplicate_dropped`；
  - `aggregation`: 每片 `{specimen_code, temperature, glaze, measure_count, raw_values, mean}`；
  - `residuals` 改按试片：`{specimen_code, fitted, residual, measure_count}`。
  - 零残差判定的规模因子由「原始行数」改为「独立试片数」，阈值语义不变。
- 指纹快照（`run_service`）：
  - `algorithm: 'balanced-fixed-anova-holm-v2'`；
  - `rows` 改为含 `measure_no` 的完整原始读数，按 `(specimen_code, measure_no)` 稳定排序；
  - 新增 `aggregation_basis: 'specimen_mean_v1'` 字段，明示聚合口径；
  - 效果：原值变化即使均值相同，`rows` 变化 → SHA256 变化（满足硬性要求）。
- 旧 run 的 `result` JSON 原样保留（v1 指纹、旧 residuals 结构），前端读取需对缺字段容错。

### 3.5 读取接口（页面核对依据）

- `GET /readings?study_id=&cell_id=&view=raw|aggregated&offset=&limit=`
  - `raw`（默认）：去重后原始读数，列含 `measure_no`，按 `(specimen_code, measure_no)` 排序；
  - `aggregated`：每试片一行，含 `measure_count`、`raw_values`（数组）、`strength_mpa`（均值）；
  - `total` 分别为原始读数条数 / 独立试片数。
- `GET /cells`：`n` = 独立试片数；新增 `raw_reading_count`；mean/std 基于试片均值（与 ANOVA 同口径），`CellSummary` 加可选字段。
- 两接口均只读，viewer 可用。

## 4. 前端设计

- `types/domain.ts`：`Reading` 加 `measure_no?`；新增 `AggregatedReading { specimen_code,temperature,glaze,strength_mpa,measure_count,raw_values:number[] }`；`Cell` 加 `raw_reading_count?`；`Result` 加 `measure_mode/raw_reading_count/specimen_count/duplicate_dropped/aggregation?`，residuals 项加可选 `measure_count`。
- `api/readings.ts` 与 `samples` store：支持 `view` 参数，分别存 `rawRows`/`aggregatedRows` 与各自 total。
- `Data.vue`：
  - 导入区说明改为支持可选 `measure_no` 列，给出表头示例与去重/拒收规则提示；textarea 默认表头更新。
  - 读数区增加「原始读数 / 试片聚合」切换；原始视图表格加「测次号」列；聚合视图显示试片、测次数、原值列表（小字号换行）、均值。
  - 分页文案区分「条原始读数 / 片独立试片」。
- `CellMatrix.vue`：`n=独立试片`，附原始读数计数（如有复测）。
- `RunSummary.vue`：显示独立试片数、原始读数条数、去重条数与模式徽标；对旧结果（无新字段）降级为原展示。
- `Results.vue`：指纹旁标注算法版本与聚合口径；新增可折叠「聚合依据」小表（取 `result.aggregation`，旧结果无此块则不显示）。
- 文案：把「当前不接受重复测量」改为「同片多测次先均值化，样本按独立试片计」。

## 5. 兼容与迁移清单

| 场景 | 行为 |
|---|---|
| 旧 CSV（无 measure_no） | 默认测次 1，结果与 v1 数值一致；新跑 run 指纹为 v2（快照结构升级），旧 run 指纹不变 |
| 旧数据库 | 执行 `migrations/002_repeat_measures.sql`；不执行则新代码插入缺列会报错，README 注明 |
| 旧 run.result / 获批方案 CSV | 不改 JSON、不改导出；前端全部字段可选容错 |
| seed 脚本 | 模型 default=1，无需改数据；补一个含复测的第四份演示试验 `BH-REP`（每格部分试片 2 测次，含一条同值重复登记），验证全链路 |
| 自然键 | 文档更新；运行名/提案标题等其余自然键不变 |

## 6. 测试计划（新建 `backend/tests/`，纯函数 + sqlite 内存库，不依赖 docker）

1. `test_aggregation.py`
   - 同片两测次异值 → 聚合均值正确、`measure_count=2`；
   - 同 `(code,measure_no)` 同值重复 → 去重计数、行数不增；
   - 同 `(code,measure_no)` 异值 → 抛错且信息含试片号；
   - 同片跨格 → 抛错；
   - 无 `measure_no` 键的旧行 → 默认 1。
2. `test_design_validation.py`：聚合后缺格/不平衡/每格<3/非有限值的失败态；样本数按试片不按读数行。
3. `test_anova_repeat.py`：构造「每片 2 测次、测次均值等于旧单测次值」的数据，断言 ANOVA 各 SS/p/对比与单测次版完全一致；再构造「均值相同、原值不同」两份数据，断言指纹不同而 ANOVA 数值相同。
4. `test_import_transaction.py`（sqlite in-memory）：冲突导入后 study/cell/reading 计数均为 0；合法导入原始行与聚合接口内容正确。
5. `test_legacy_fingerprint.py`：固定一份旧结构输入，用 v1 快照构造方式回归断言其哈希不变（保护历史复算口径）。
运行：`python -m pytest backend/tests -q`（requirements 加 `pytest`）。

## 7. 文档与收尾

- README：CSV 表头、统计口径（聚合先于分析、n 的定义）、去重/拒收规则、指纹 v2 说明、迁移步骤、seed 新试验说明。
- `migrations/README.md`：Schema v2 自然键与手工 DDL 说明。
- 前端构建 `npm run build` 做类型检查；后端 `python -m py_compile` 全量编译；跑 pytest。
- 提交粒度：①后端模型/迁移/聚合/分析 ②接口与 seed ③前端 ④文档与测试；提交信息带 Co-Authored-By。

## 8. 风险与取舍

- **均值化与信息损失**：测次内仪器波动不进入 MSE，这是「独立试片才是实验单位」的正确口径；页面保留全部原值与测次数以供核对，不做静默平均。
- **v1/v2 指纹并存**：重跑旧试验会得到 v2 新指纹，属预期（快照口径显式升级）；历史 run 与方案引用的旧指纹仍可从 JSON 复算。
- **MySQL 迁移无自动化框架**：沿用项目现状提供版本化 SQL + 文档，不引入 Alembic。
- **3000 行上限**：仍按原始读数行限制，复测多的试验独立试片数会更少，避免放大接口与计算负担。
