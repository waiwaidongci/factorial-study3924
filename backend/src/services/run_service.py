import json,hashlib
from sqlalchemy import select
from fastapi import HTTPException
from redis import Redis
from src.config.settings import REDIS_URL
from src.models import FactorStudy,FactorRun
from src.services.reading_service import raw_readings
from src.services.anova import analyze_factorial
from src.constants.enums import RunStatus
queue=Redis.from_url(REDIS_URL)
def list_runs(db):return db.scalars(select(FactorRun).order_by(FactorRun.id.desc())).all()
def get_run(db,id):
    run=db.get(FactorRun,id)
    if not run:raise HTTPException(404,'分析运行不存在')
    return run
def create_run(db,data):
    if not db.get(FactorStudy,data.study_id):raise HTTPException(404,'试验不存在')
    if db.scalar(select(FactorRun).where(FactorRun.name==data.name)):raise HTTPException(409,'运行名称已存在')
    item=FactorRun(**data.model_dump(),status=RunStatus.QUEUED);db.add(item);db.commit();queue.lpush('factorial:runs',str(item.id));return item
def execute_run(db,id):
    run=db.get(FactorRun,id)
    if not run or run.status not in (RunStatus.QUEUED,RunStatus.RUNNING):return
    run.status=RunStatus.RUNNING;db.commit()
    try:
        study=db.get(FactorStudy,run.study_id);rows=raw_readings(db,study.id);result=analyze_factorial(rows,study.a_levels,study.b_levels,run.alpha)
        # 指纹保留含测次号的全部原始读数：原值变化即使试片均值相同，哈希也必然变化
        fingerprint_rows=sorted(({'specimen_code':r['specimen_code'],'measure_no':r.get('measure_no',1),'temperature':r['temperature'],'glaze':r['glaze'],'strength_mpa':r['strength_mpa']} for r in rows),key=lambda r:(r['specimen_code'],r['measure_no']))
        snapshot={'algorithm':'balanced-fixed-anova-holm-v2','aggregation_basis':'specimen_mean_v1','study_code':study.code,'a_levels':study.a_levels,'b_levels':study.b_levels,'rows':fingerprint_rows,'alpha':run.alpha,'contrast_family':run.contrast_family}
        result['fingerprint']=hashlib.sha256(json.dumps(snapshot,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest();result['study_name']=study.name;result['study_code']=study.code
        run.result=result;run.status=RunStatus.COMPLETED;run.error='';db.commit()
    except Exception as exc:
        db.rollback();run=db.get(FactorRun,id);run.status=RunStatus.FAILED;run.error=str(exc)[:600];db.commit()
