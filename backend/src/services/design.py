from collections import Counter
import numpy as np
def validate_design(rows,a_levels,b_levels):
    if len(a_levels)<2 or len(b_levels)<2 or len(set(a_levels))!=len(a_levels) or len(set(b_levels))!=len(b_levels):raise ValueError('两因子均需至少两个唯一水平')
    expected={(a,b) for a in a_levels for b in b_levels};counts=Counter((r['temperature'],r['glaze']) for r in rows)
    if set(counts)!=expected:raise ValueError('完整交叉设计缺格或包含未声明水平')
    if len(set(counts.values()))!=1:raise ValueError('只接受每格样本数相同的平衡设计')
    n=next(iter(counts.values()))
    if n<3:raise ValueError('每格至少3个独立试片')
    if len({r['specimen_code'] for r in rows})!=len(rows):raise ValueError('试片编号在整个试验内必须唯一；不接受重复测量')
    if not np.isfinite([r['strength_mpa'] for r in rows]).all():raise ValueError('测量值必须有限')
    return n
