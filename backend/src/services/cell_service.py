import numpy as np
from sqlalchemy import select
from fastapi import HTTPException
from src.models import FactorStudy,TrialCell,TrialReading
def list_cells(db,study_id):
    if not db.get(FactorStudy,study_id):raise HTTPException(404,'试验不存在')
    cells=db.scalars(select(TrialCell).where(TrialCell.study_id==study_id).order_by(TrialCell.id)).all();result=[]
    for c in cells:
        values=db.scalars(select(TrialReading.strength_mpa).where(TrialReading.cell_id==c.id)).all();result.append({'id':c.id,'study_id':c.study_id,'temperature':c.temperature,'glaze':c.glaze,'n':len(values),'mean':float(np.mean(values)),'std':float(np.std(values,ddof=1))})
    return result
