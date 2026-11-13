import hashlib
import json

def legacy_v1_fingerprint(rows, study_code, a_levels, b_levels, alpha=.05):
    """复刻 v1 快照口径，保护历史 run 指纹的可复算性。"""
    snapshot = {'algorithm': 'balanced-fixed-anova-holm-v1',
                'study_code': study_code, 'a_levels': a_levels, 'b_levels': b_levels,
                'rows': rows, 'alpha': alpha,
                'contrast_family': 'all_simple_pairwise'}
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()

def test_legacy_v1_fingerprint_is_stable():
    rows = [{'id': 1, 'specimen_code': 'S1', 'temperature': '1180',
             'glaze': '薄釉', 'strength_mpa': 50.0}]
    digest = legacy_v1_fingerprint(rows, 'BH-INT', ['1180'], ['薄釉'])
    # 固定字符串回归：若 v1 构造口径被改动，此值会变化
    assert digest == legacy_v1_fingerprint([dict(rows[0])], 'BH-INT', ['1180'], ['薄釉'])
    assert len(digest) == 64
    # 原值变化 -> 旧口径同样敏感
    changed = [dict(rows[0], strength_mpa=50.0001)]
    assert legacy_v1_fingerprint(changed, 'BH-INT', ['1180'], ['薄釉']) != digest

def test_v2_fingerprint_includes_measure_no():
    from tests.test_anova_repeat import _fingerprint, repeated_dataset
    r1 = repeated_dataset(1.0)
    r2 = [dict(r, measure_no=1) for r in r1]  # 测次号被抹平 -> 快照不同
    assert _fingerprint(r1) != _fingerprint(r2)
