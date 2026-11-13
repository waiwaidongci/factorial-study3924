from sqlalchemy import select
from fastapi import HTTPException
from src.models import FactorStudy,TrialCell,TrialReading
from src.services.aggregation import aggregate_specimens
def _query(db,study_id):
    return db.execute(select(TrialReading,TrialCell).join(TrialCell,TrialReading.cell_id==TrialCell.id).where(TrialReading.study_id==study_id).order_by(TrialReading.specimen_code,TrialReading.measure_no)).all()
def raw_readings(db,study_id):
    return [{'id':r.id,'specimen_code':r.specimen_code,'measure_no':r.measure_no,'temperature':c.temperature,'glaze':c.glaze,'strength_mpa':r.strength_mpa} for r,c in _query(db,study_id)]
def list_readings(db,study_id,cell_id,offset,limit,view='raw'):
    if not db.get(FactorStudy,study_id):raise HTTPException(404,'试验不存在')
    rows=raw_readings(db,study_id)
    if cell_id:
        c=db.get(TrialCell,cell_id)
        if not c or c.study_id!=study_id:raise HTTPException(404,'处理格不属于当前试验')
        rows=[r for r in rows if r['temperature']==c.temperature and r['glaze']==c.glaze]
    if view=='aggregated':
        aggregated,_=aggregate_specimens(rows)
        payload=[{'specimen_code':r['specimen_code'],'temperature':r['temperature'],'glaze':r['glaze'],'strength_mpa':r['strength_mpa'],'measure_count':r['measure_count'],'measure_nos':r['measure_nos'],'raw_values':r['raw_values']} for r in aggregated]
        return {'view':'aggregated','total':len(payload),'rows':payload[offset:offset+limit]}
    return {'view':'raw','total':len(rows),'rows':rows[offset:offset+limit]}
