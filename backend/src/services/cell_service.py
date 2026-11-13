import numpy as np
from sqlalchemy import select
from fastapi import HTTPException
from src.models import FactorStudy,TrialCell,TrialReading
from src.services.aggregation import aggregate_specimens
from src.services.reading_service import raw_readings
def list_cells(db,study_id):
    if not db.get(FactorStudy,study_id):raise HTTPException(404,'试验不存在')
    cells=db.scalars(select(TrialCell).where(TrialCell.study_id==study_id).order_by(TrialCell.id)).all()
    aggregated,_=aggregate_specimens(raw_readings(db,study_id))
    result=[]
    for c in cells:
        raw_values=db.scalars(select(TrialReading.strength_mpa).where(TrialReading.cell_id==c.id)).all()
        specimen_means=[r['strength_mpa'] for r in aggregated if r['temperature']==c.temperature and r['glaze']==c.glaze]
        result.append({'id':c.id,'study_id':c.study_id,'temperature':c.temperature,'glaze':c.glaze,'n':len(specimen_means),'raw_reading_count':len(raw_values),'mean':float(np.mean(specimen_means)),'std':float(np.std(specimen_means,ddof=1))})
    return result
