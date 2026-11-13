from sqlalchemy import select
from fastapi import HTTPException
from src.models import FactorStudy,TrialCell,TrialReading
def raw_readings(db,study_id):
    return [{'id':r.id,'specimen_code':r.specimen_code,'temperature':c.temperature,'glaze':c.glaze,'strength_mpa':r.strength_mpa} for r,c in db.execute(select(TrialReading,TrialCell).join(TrialCell,TrialReading.cell_id==TrialCell.id).where(TrialReading.study_id==study_id).order_by(TrialReading.specimen_code)).all()]
def list_readings(db,study_id,cell_id,offset,limit):
    if not db.get(FactorStudy,study_id):raise HTTPException(404,'试验不存在')
    rows=raw_readings(db,study_id)
    if cell_id:
        c=db.get(TrialCell,cell_id)
        if not c or c.study_id!=study_id:raise HTTPException(404,'处理格不属于当前试验')
        rows=[r for r in rows if r['temperature']==c.temperature and r['glaze']==c.glaze]
    return {'total':len(rows),'rows':rows[offset:offset+limit]}
