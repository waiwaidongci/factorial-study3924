import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from src.config.database import Base
from src.models import FactorStudy, TrialCell, TrialReading
from src.schemas.study import StudyInput
from src.services.study_service import create_study
from src.services.reading_service import list_readings

A = ['1180', '1220']
B = ['薄釉', '厚釉']

@pytest.fixture()
def session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    yield s
    s.close()

def csv_text(lines):
    return 'specimen_code,temperature,glaze,strength_mpa,measure_no\n' + '\n'.join(lines)

def good_lines():
    lines = []
    k = 0
    for t in A:
        for g in B:
            for i in range(4):
                k += 1
                code = f'S{k:02d}'
                lines.append(f'{code},{t},{g},{50 + i},1')
                if i % 2 == 0:
                    lines.append(f'{code},{t},{g},{52 + i},2')
    return lines

def payload(csv_text_value, code='T1'):
    return StudyInput(code=code, name='试验' + code, a_levels=A, b_levels=B,
                      source_file='inst.csv', note='', csv_text=csv_text_value)

def test_conflict_leaves_no_residual_rows(session):
    lines = good_lines()
    # 制造同片同测次异值冲突
    lines.append('S01,1180,薄釉,99.9,1')
    with pytest.raises(HTTPException) as exc:
        create_study(session, payload(csv_text(lines)))
    assert exc.value.status_code == 422
    assert session.scalar(select(func.count()).select_from(FactorStudy)) == 0
    assert session.scalar(select(func.count()).select_from(TrialCell)) == 0
    assert session.scalar(select(func.count()).select_from(TrialReading)) == 0

def test_cross_cell_rejection_is_atomic(session):
    lines = good_lines()
    lines.append('S01,1220,薄釉,60.0,3')
    with pytest.raises(HTTPException) as exc:
        create_study(session, payload(csv_text(lines)))
    assert exc.value.status_code == 422
    assert session.scalar(select(func.count()).select_from(TrialReading)) == 0

def test_valid_import_dedupes_and_aggregates(session):
    lines = good_lines()
    # 同值重复登记一条
    lines.append('S01,1180,薄釉,50,1')
    out = create_study(session, payload(csv_text(lines)))
    assert out['specimen_count'] == 16
    assert out['duplicate_dropped'] == 1
    # 原始读数：每格4片，其中2片双测次 -> 每格6条，共24条
    assert session.scalar(select(func.count()).select_from(TrialReading)) == 24
    raw = list_readings(session, out['id'], None, 0, 200, 'raw')
    assert raw['total'] == 24 and raw['view'] == 'raw'
    assert all('measure_no' in r for r in raw['rows'])
    agg = list_readings(session, out['id'], None, 0, 200, 'aggregated')
    assert agg['total'] == 16 and agg['view'] == 'aggregated'
    s01 = next(r for r in agg['rows'] if r['specimen_code'] == 'S01')
    assert s01['measure_count'] == 2
    assert s01['raw_values'] == [50.0, 52.0]
    assert s01['strength_mpa'] == 51.0

def test_legacy_csv_without_measure_no_column(session):
    lines = []
    k = 0
    for t in A:
        for g in B:
            for i in range(3):
                k += 1
                lines.append(f'L{k:02d},{t},{g},{48 + i}')
    text = 'specimen_code,temperature,glaze,strength_mpa\n' + '\n'.join(lines)
    out = create_study(session, payload(text, code='LEG'))
    assert out['specimen_count'] == 12
    raw = list_readings(session, out['id'], None, 0, 200, 'raw')
    assert all(r['measure_no'] == 1 for r in raw['rows'])

def test_unknown_column_rejected(session):
    text = ('specimen_code,temperature,glaze,strength_mpa,operator\n'
            'X1,1180,薄釉,50\nX2,1180,厚釉,51\n')
    with pytest.raises(HTTPException) as exc:
        create_study(session, payload(text, code='BAD'))
    assert exc.value.status_code == 422
    assert '未知列' in exc.value.detail

def test_bom_prefixed_legacy_csv_imports(session):
    lines = []
    k = 0
    for t in A:
        for g in B:
            for i in range(3):
                k += 1
                lines.append(f'L{k:02d},{t},{g},{48 + i}')
    text = '﻿specimen_code,temperature,glaze,strength_mpa\n' + '\n'.join(lines)
    out = create_study(session, payload(text, code='BOM'))
    assert out['specimen_count'] == 12
