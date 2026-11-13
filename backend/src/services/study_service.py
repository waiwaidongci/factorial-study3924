import csv,io
from sqlalchemy import select,func
from fastapi import HTTPException
from pydantic import ValidationError
from src.models import FactorStudy,TrialCell,TrialReading
from src.schemas.reading import ReadingInput
from src.services.design import validate_design
def list_studies(db):
    result=[]
    for s in db.scalars(select(FactorStudy).order_by(FactorStudy.id)).all():
        count=db.scalar(select(func.count()).select_from(TrialReading).where(TrialReading.study_id==s.id));result.append({'id':s.id,'code':s.code,'name':s.name,'a_levels':s.a_levels,'b_levels':s.b_levels,'source_file':s.source_file,'note':s.note,'row_count':count})
    return result
def create_study(db,data):
    if db.scalar(select(FactorStudy).where(FactorStudy.code==data.code)):raise HTTPException(409,'试验编号已存在')
    try:
        rows=[ReadingInput.model_validate(r) for r in csv.DictReader(io.StringIO(data.csv_text))]
        if len(rows)>3000:raise ValueError('每份试验最多3000个试片')
        validate_design([r.model_dump() for r in rows],data.a_levels,data.b_levels)
    except (ValidationError,ValueError,csv.Error) as exc:raise HTTPException(422,str(exc)[:500])
    item=FactorStudy(**data.model_dump(exclude={'csv_text'}));db.add(item);db.flush();cells={}
    for a in data.a_levels:
        for b in data.b_levels:
            c=TrialCell(study_id=item.id,temperature=a,glaze=b);db.add(c);db.flush();cells[(a,b)]=c.id
    db.add_all([TrialReading(study_id=item.id,cell_id=cells[(r.temperature,r.glaze)],specimen_code=r.specimen_code,strength_mpa=r.strength_mpa) for r in rows]);db.commit();return {'id':item.id,'row_count':len(rows)}
