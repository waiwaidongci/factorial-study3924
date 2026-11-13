import pytest
from src.services.design import prepare_observations

A = ['1180', '1220']
B = ['薄釉', '厚釉']

def row(code, value, measure_no=1, temp='1180', glaze='薄釉'):
    return {'specimen_code': code, 'temperature': temp, 'glaze': glaze,
            'strength_mpa': float(value), 'measure_no': measure_no}

def balanced_rows(n_per_cell, repeated=()):
    rows = []
    k = 0
    for t in A:
        for g in B:
            for i in range(n_per_cell):
                k += 1
                code = f'S{k:03d}'
                rows.append(row(code, 50 + i, 1, t, g))
                if code in repeated:
                    rows.append(row(code, 52 + i, 2, t, g))
    return rows

def test_balanced_repeated_design_counts_specimens_not_rows():
    repeated = {f'S{i:03d}' for i in (1, 7)}
    rows = balanced_rows(4, repeated)
    agg, audit, n = prepare_observations(rows, A, B)
    assert n == 4                      # 每格独立试片 4
    assert len(agg) == 16             # 总试片 16
    assert audit['raw_count'] == 18   # 原始读数 18（两条复测）
    assert audit['measure_mode'] == 'repeated'

def test_missing_cell_rejected():
    rows = [r for r in balanced_rows(3) if not (r['temperature'] == '1220' and r['glaze'] == '厚釉')]
    with pytest.raises(ValueError, match='缺格'):
        prepare_observations(rows, A, B)

def test_unbalanced_after_aggregation_rejected():
    rows = balanced_rows(4)
    rows = [r for r in rows if r['specimen_code'] != 'S001']
    with pytest.raises(ValueError, match='平衡'):
        prepare_observations(rows, A, B)

def test_less_than_three_specimens_rejected_even_with_many_measures():
    # 每格只有 2 个试片，但每个试片 3 个测次 -> 行数够多仍应拒收
    rows = balanced_rows(2)
    extra = []
    for r in list(rows):
        extra.append(row(r['specimen_code'], r['strength_mpa'] + 1, 2, r['temperature'], r['glaze']))
        extra.append(row(r['specimen_code'], r['strength_mpa'] + 2, 3, r['temperature'], r['glaze']))
    with pytest.raises(ValueError, match='至少3个独立试片'):
        prepare_observations(rows + extra, A, B)

def test_non_finite_rejected():
    rows = balanced_rows(3)
    rows[0]['strength_mpa'] = float('nan')
    with pytest.raises(ValueError, match='有限'):
        prepare_observations(rows, A, B)
