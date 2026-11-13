import copy
from src.services.anova import analyze_factorial

A = ['1180', '1220']
B = ['薄釉', '厚釉']

def single_dataset():
    # 每格 4 个独立试片，单测次
    values = {
        ('1180', '薄釉'): [48.0, 49.5, 50.2, 51.0],
        ('1180', '厚釉'): [55.0, 56.1, 57.2, 54.8],
        ('1220', '薄釉'): [58.0, 59.4, 60.1, 57.6],
        ('1220', '厚釉'): [62.0, 63.3, 61.7, 64.1],
    }
    rows = []
    k = 0
    for cell, vals in values.items():
        for v in vals:
            k += 1
            rows.append({'specimen_code': f'S{k:02d}', 'measure_no': 1,
                         'temperature': cell[0], 'glaze': cell[1], 'strength_mpa': v})
    return rows

def repeated_dataset(split):
    # 每片拆成两个测次，均值严格等于单测次数据
    rows = []
    for r in single_dataset():
        m = r['strength_mpa']
        d = split
        rows.append({**r, 'measure_no': 1, 'strength_mpa': m - d})
        rows.append({**r, 'measure_no': 2, 'strength_mpa': m + d})
    return rows

def test_anova_identical_after_mean_aggregation():
    single = analyze_factorial(single_dataset(), A, B)
    repeated = analyze_factorial(repeated_dataset(1.5), A, B)
    assert repeated['per_cell'] == single['per_cell'] == 4
    assert repeated['n'] == single['n'] == 16
    assert repeated['raw_reading_count'] == 32
    assert repeated['specimen_count'] == 16
    assert repeated['measure_mode'] == 'repeated'
    for key in ('grand_mean', 'mse', 'df_error'):
        assert repeated[key] == single[key]
    for t1, t2 in zip(single['anova'], repeated['anova']):
        assert t1['ss'] == t2['ss'] and t1['df'] == t2['df'] and t1['p'] == t2['p']
    for c1, c2 in zip(single['contrasts'], repeated['contrasts']):
        assert c1['estimate'] == c2['estimate'] and c1['p_raw'] == c2['p_raw']
        assert c1['p_holm'] == c2['p_holm']

def _fingerprint(rows):
    import hashlib, json
    fingerprint_rows = sorted(
        ({'specimen_code': r['specimen_code'], 'measure_no': r.get('measure_no', 1),
          'temperature': r['temperature'], 'glaze': r['glaze'],
          'strength_mpa': r['strength_mpa']} for r in rows),
        key=lambda r: (r['specimen_code'], r['measure_no']))
    snapshot = {'algorithm': 'balanced-fixed-anova-holm-v2',
                'aggregation_basis': 'specimen_mean_v1',
                'rows': fingerprint_rows}
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()

def test_same_mean_different_raw_values_changes_fingerprint_only():
    r1 = repeated_dataset(1.0)
    r2 = repeated_dataset(2.0)
    a1, a2 = analyze_factorial(r1, A, B), analyze_factorial(r2, A, B)
    # 均值完全一致 -> 分析数值一致
    assert a1['mse'] == a2['mse']
    assert a1['anova'][0]['ss'] == a2['anova'][0]['ss']
    # 原值不同 -> 指纹不同
    assert _fingerprint(r1) != _fingerprint(r2)
    # 同一份数据指纹稳定
    assert _fingerprint(copy.deepcopy(r1)) == _fingerprint(r1)

def test_aggregation_basis_exposed():
    result = analyze_factorial(repeated_dataset(0.5), A, B)
    assert len(result['aggregation']) == 16
    first = result['aggregation'][0]
    assert set(first) == {'specimen_code', 'temperature', 'glaze', 'measure_count',
                          'measure_nos', 'raw_values', 'mean'}
    assert first['measure_count'] == 2
    assert all(r['measure_count'] == 2 for r in result['residuals'])
