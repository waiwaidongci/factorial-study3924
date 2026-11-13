from collections import Counter
import numpy as np
from src.services.aggregation import aggregate_specimens

def prepare_observations(rows,a_levels,b_levels):
    """原始读数 -> (聚合后每试片一行的观测, 聚合审计, 每格独立试片数 n)。"""
    if len(a_levels)<2 or len(b_levels)<2 or len(set(a_levels))!=len(a_levels) or len(set(b_levels))!=len(b_levels):raise ValueError('两因子均需至少两个唯一水平')
    if not np.isfinite([r['strength_mpa'] for r in rows]).all():raise ValueError('测量值必须有限')
    aggregated,audit=aggregate_specimens(rows)
    if not aggregated:raise ValueError('CSV没有有效读数')
    expected={(a,b) for a in a_levels for b in b_levels}
    counts=Counter((r['temperature'],r['glaze']) for r in aggregated)
    if set(counts)!=expected:raise ValueError('完整交叉设计缺格或包含未声明水平')
    if len(set(counts.values()))!=1:raise ValueError('只接受每格独立试片数相同的平衡设计（样本按独立试片计，不按测次行数计）')
    n=next(iter(counts.values()))
    if n<3:raise ValueError('每格至少3个独立试片（同片多测次先取均值，不重复计样本）')
    if len({r['specimen_code'] for r in aggregated})!=len(aggregated):raise ValueError('试片编号在整个试验内必须唯一')
    return aggregated,audit,n

def validate_design(rows,a_levels,b_levels):
    return prepare_observations(rows,a_levels,b_levels)[2]
