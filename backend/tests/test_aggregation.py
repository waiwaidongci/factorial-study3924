import pytest
from src.services.aggregation import aggregate_specimens, check_columns

A = ['1180', '1220']
B = ['薄釉', '厚釉']

def row(code, value, measure_no=1, temp='1180', glaze='薄釉'):
    return {'specimen_code': code, 'temperature': temp, 'glaze': glaze,
            'strength_mpa': value, 'measure_no': measure_no}

def test_mean_of_two_measures():
    rows = [row('S1', 10.0, 1), row('S1', 20.0, 2)]
    agg, audit = aggregate_specimens(rows)
    assert len(agg) == 1
    assert agg[0]['strength_mpa'] == 15.0
    assert agg[0]['measure_count'] == 2
    assert agg[0]['raw_values'] == [10.0, 20.0]
    assert audit['measure_mode'] == 'repeated'
    assert audit['specimen_count'] == 1
    assert audit['raw_count'] == 2

def test_duplicate_same_value_deduped():
    rows = [row('S1', 12.5, 1), row('S1', 12.5, 1)]
    agg, audit = aggregate_specimens(rows)
    assert len(agg) == 1
    assert agg[0]['measure_count'] == 1
    assert audit['duplicate_dropped'] == 1
    assert audit['deduped_count'] == 1

def test_same_measure_conflicting_values_rejected():
    rows = [row('S1', 12.5, 1), row('S1', 13.0, 1)]
    with pytest.raises(ValueError, match='S1'):
        aggregate_specimens(rows)

def test_specimen_across_cells_rejected():
    rows = [row('S1', 12.5, 1, '1180', '薄釉'),
            row('S1', 12.5, 2, '1220', '薄釉')]
    with pytest.raises(ValueError, match='跨处理格'):
        aggregate_specimens(rows)

def test_missing_measure_no_defaults_to_one():
    rows = [{'specimen_code': 'S1', 'temperature': '1180', 'glaze': '薄釉', 'strength_mpa': 9.0}]
    agg, audit = aggregate_specimens(rows)
    assert agg[0]['measure_nos'] == [1]
    assert audit['measure_mode'] == 'single'

def test_column_whitelist():
    with pytest.raises(ValueError, match='未知列'):
        check_columns(['specimen_code', 'temperature', 'glaze', 'strength_mpa', 'stray'])
    with pytest.raises(ValueError, match='缺少必需列'):
        check_columns(['specimen_code', 'temperature', 'glaze'])
    check_columns(['specimen_code', 'temperature', 'glaze', 'strength_mpa'])
    check_columns(['specimen_code', 'temperature', 'glaze', 'strength_mpa', 'measure_no'])
