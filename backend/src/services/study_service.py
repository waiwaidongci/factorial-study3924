import csv,io
from sqlalchemy import select,func
from fastapi import HTTPException
from pydantic import ValidationError
from src.models import FactorStudy,TrialCell,TrialReading
from src.schemas.reading import ReadingInput
from src.services.aggregation import check_columns
from src.services.design import prepare_observations
MAX_RAW_ROWS=3000
def list_studies(db):
    result=[]
    for s in db.scalars(select(FactorStudy).order_by(FactorStudy.id)).all():
        count=db.scalar(select(func.count()).select_from(TrialReading).where(TrialReading.study_id==s.id));result.append({'id':s.id,'code':s.code,'name':s.name,'a_levels':s.a_levels,'b_levels':s.b_levels,'source_file':s.source_file,'note':s.note,'row_count':count})
    return result
def _parse_csv(csv_text):
    if csv_text.startswith('﻿'):csv_text=csv_text[1:]  # 兼容带 BOM 的导出文件回传
    reader=csv.DictReader(io.StringIO(csv_text))
    check_columns(reader.fieldnames)
    raw_dicts=[]
    for row in reader:
        if row.get(None):raise ValueError('CSV存在列数超出表头的行')
        # 旧表无 measure_no 或该格留空 -> 默认第 1 测次
        if row.get('measure_no') is None or str(row.get('measure_no')).strip()=='' :row['measure_no']='1'
        raw_dicts.append(row)
    return raw_dicts
def create_study(db,data):
    if db.scalar(select(FactorStudy).where(FactorStudy.code==data.code)):raise HTTPException(409,'试验编号已存在')
    try:
        raw_dicts=_parse_csv(data.csv_text)
        rows=[ReadingInput.model_validate(r) for r in raw_dicts]
        if len(rows)>MAX_RAW_ROWS:raise ValueError(f'每份试验最多{MAX_RAW_ROWS}条原始读数（含各测次）')
        # 全部设计/冲突校验先于任何写库；失败即抛错，不留残项
        _,audit,_=prepare_observations([r.model_dump() for r in rows],data.a_levels,data.b_levels)
        # 去重后的原始读数（校验已保证同片同测次重复行同值，异值会在上面整份拒收）
        seen=set();deduped_rows=[]
        for r in rows:
            key=(r.specimen_code,r.measure_no)
            if key in seen:continue
            seen.add(key);deduped_rows.append(r)
    except (ValidationError,ValueError,csv.Error) as exc:raise HTTPException(422,str(exc)[:500])
    item=FactorStudy(**data.model_dump(exclude={'csv_text'}));db.add(item);db.flush();cells={}
    for a in data.a_levels:
        for b in data.b_levels:
            c=TrialCell(study_id=item.id,temperature=a,glaze=b);db.add(c);db.flush();cells[(a,b)]=c.id
    db.add_all([TrialReading(study_id=item.id,cell_id=cells[(r.temperature,r.glaze)],specimen_code=r.specimen_code,measure_no=r.measure_no,strength_mpa=r.strength_mpa) for r in deduped_rows]);db.commit()
    return {'id':item.id,'row_count':len(deduped_rows),'specimen_count':audit['specimen_count'],'duplicate_dropped':audit['duplicate_dropped']}
