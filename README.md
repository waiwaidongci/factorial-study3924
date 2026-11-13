# 焙衡窑烧因子实验簿 · Factorial Study

把完整平衡的温度×釉层试验变成可复算的因子、交互与预设对比，再形成经过审批的独立复烧方案。

焙衡陶瓷材料组有14位实验分析员。过去只比较总均值，温度与釉层的交互被忽略，重复测量混进独立试片，事后只挑显著对比。本项目接收随机独立试片的抗折强度，替代设计核对、固定效应分析与后续试验归档，下游工艺观察员据此准备新的独立验证。数据为模拟陶瓷材料试验，不直接产生量产结论。

## 启动与账号

```sh
cp .env.example .env
docker compose up -d --build
docker compose ps
docker compose exec -T backend python -m scripts.seed_demo
```

前端 http://localhost:18221，后端 http://localhost:19221，API文档 http://localhost:19221/docs。Nginx去掉`/api/`前缀代理，直接访问后端时不带`/api`。结束：`docker compose down -v --remove-orphans`（删除本项目演示数据库与卷）。

共用密码`Beiheng2026!`。

| 邮箱 | 角色 | 页面/权限/典型动作 |
|---|---|---|
| admin@beiheng.demo | admin / 实验负责人 | 六页；导入、分析、提案、审批、导出 |
| analyst@beiheng.demo | analyst / 材料分析员 | 六页；导入、分析、提案、导出；不能审批 |
| viewer@beiheng.demo | viewer / 工艺观察员 | 六页只读，下载获批完整CSV；不能写入和审批 |

JWT有效8小时，带盐PBKDF2-SHA256密码，独立审计/错误中间件；登录每来源每分钟30次。对外部署前替换演示凭证及签名密钥。

## 一天的实验剧本

1. 09:00 梁衡登录，打开`bh-kiln-bh-int.csv`，核对1180/1220/1260°C与薄釉/厚釉六格。
2. 09:05 每格20个独立试片，共120片；检查BH1-11-01等编号及强度MPa。
3. 09:10 建立分析记录，alpha=.05，固定全部简单效应家族。
4. 09:12 worker计算ANOVA，统一格内MSE和残差自由度，再计算全部9个预设差异。
5. 09:15 读取交互图与ANOVA；交互有证据时，以条件差异解释温度作用。
6. 09:20 查看9项原始p/Holm p、逐项t区间，包括未拒绝的对比。
7. 09:30 围绕1220°C釉层条件拟定独立复烧，重新随机分配试片并记录窑位/批次。
8. 10:00 陶焙审批；程砚下载5行ANOVA与全部9项对比的完整CSV及输入指纹。

## 设计与统计口径

每份试验声明温度水平和釉层水平；只接受完整平衡交叉设计，每格至少3个独立观测，试片编号在全试验唯一。固定因子，当前不用于重复测量、随机窑批或不平衡设计。CSV表头为`specimen_code,temperature,glaze,strength_mpa`；强度为有限正数，最多3000行。导入后原数据不修改，需要更正时建立新试验。

设A有a水平，B有b水平，每格n个观测，处理均值mᵢⱼ、总体均值m、边际均值mᵢ·/m·ⱼ：

- `SS_A=bn Σ(mᵢ·−m)²`，df=a−1。
- `SS_B=an Σ(m·ⱼ−m)²`，df=b−1。
- `SS_AB=n Σ(mᵢⱼ−mᵢ·−m·ⱼ+m)²`，df=(a−1)(b−1)。
- `SS_E=Σ(yᵢⱼₖ−mᵢⱼ)²`，df=ab(n−1)，MSE=SS_E/df_E。
- 各效应`F=MS_effect/MSE`，用对应F分布右尾概率。校正总SS由四部分相加核验。

公式与固定效应前提参照[NIST平衡两因子ANOVA说明](https://www.itl.nist.gov/div898/handbook/prc/section4/prc438.htm)。残差近似正态、观测独立、各格同方差是推断前提，本项目不自动证明这些前提。零或机器精度下不可分辨的残差方差返回不可估，不用无穷F冒充显著；足够小但可分辨的正残差仍可计算。

**固定简单效应家族。** 在每个B水平内列出全部A两两比较，在每个A水平内列出全部B两两比较，3×2设计共`2*C(3,2)+3*C(2,2)=9`项，不提供只挑显著项的开关。差值方向为左减右，`SE=sqrt(2*MSE/n)`，`t=差值/SE`，使用df_E双侧t概率。

Holm将全家族p从小到大排序，按剩余项数乘p后累计取不下降最大值并截到1；依据调整p<alpha判定拒绝。区间为`差值±t_(1−alpha/2,df_E)*SE`，是同方差**逐项**t区间，没有家族同时覆盖保证；p校正与区间口径分别标明。

有交互时，主效应仍是跨另一因子水平的平均效应，不直接代表每个釉层下的温度作用。无显著证据不等于差异为零；统计显著性也不替代工艺重要性和新批次验证。

## 复算、边界与seed

完整输入SHA256包含算法版本、试验code、因子水平及顺序、稳定按试片编号排序的所有读数/ID、alpha与固定家族名。源数值和alpha均为MySQL DOUBLE，结果为JSON双精度。缺格、非平衡、每格<3、重复试片、非有限值及零残差方差有真实失败态。

seed固定随机种子117：3独立试验，每个3×2×20=120片，总360片；BH-INT为交互线索、BH-ADD为加性生成对照、BH-CONST为常量边界。前两份实际计算，常量运行保留failed原因。试验code、处理格(study,temp,glaze)、试片(study,code)、运行名、提案标题和账号邮箱为自然键；重复seed不覆盖用户改动。

## 页面、实体和共享代码

六页：实验首页、处理格与试片、分析配置、因子与交互、后续实验、实验留痕。

FactorStudy、TrialCell、TrialReading、FactorRun、FollowupPlan五实体各贯穿model/schema/service/controller/route/前端API/store/页面。CellMatrix、InteractionPlot、RunSummary、RunTable、StudySelect为共享业务组件；PageHeading/StatusBadge/ErrorNotice/EmptyState通用。useTask与usePolling分别处理恢复和运行刷新。

后端枚举`backend/src/constants/enums.py`：Role、RunStatus、PlanStatus、CONTRAST_FAMILY；状态用于run_service/worker/plan_service，角色授权在utils/auth。前端`frontend/src/constants/enums.ts`：roles/statuses/family，供App、StatusBadge、配置与审批使用。

## 工程与环境

| 层 | 实现 |
|---|---|
| 前端 | Vue3.5.45、TypeScript、Pinia、Vue Router、Vite6.4.6、Nginx1.27 |
| 后端 | Python3.11、FastAPI、SQLAlchemy、PyMySQL、PyJWT |
| 计算 | NumPy、SciPy1.17.1 F/t分布；平衡SS与Holm明确实现 |
| 任务 | 单Python worker，MySQL状态为事实源，Redis唤醒，恢复queued/running |
| 存储 | MySQL8.0、Redis7 AOF |

恰好frontend/backend/worker/db/redis五服务，均有真实healthcheck。backend等db/redis；worker另等backend初始化；frontend等backend。命名卷为数据库、Redis、后端/worker共享产物，结果存DB、CSV实时生成。初始schema由metadata创建，`backend/migrations/README.md`说明自然键，尚无生产升级迁移工具。

`backend/src/{routes,controllers,services,models,schemas,middlewares,utils,constants,config}`、`backend/scripts/seed_demo.py`；`frontend/src/{api,stores,types,components/common,hooks,pages,router,utils,constants}`。

| 变量 | 默认 |
|---|---|
| COMPOSE_PROJECT_NAME | factorial-study；显式name适配中文父目录 |
| FRONTEND_PORT/BACKEND_PORT/DB_PORT | 18221/19221/17721 |
| DB_PASSWORD | 本地演示数据库密码 |
| JWT_SECRET | 项目独立签名密钥 |
| SEED_DEMO | true启动自动seed，失败记录日志且不阻塞API |

本地开发：db/redis启动后，在backend安装requirements、设置DATABASE_URL/REDIS_URL/JWT_SECRET，运行`uvicorn src.main:app --reload`与`python -m src.worker`；前端`npm ci && npm run dev`。/api默认代理19221，本地API用8000时同步调整。测试、截图及TESTING位于批次根`test-artifacts/gb-0017/`。MIT License，见LICENSE。
