"""同一独立试片的仪器复测测次聚合。

规则（与业务验收口径一致）：
- 同 (specimen_code, measure_no) 同值重复登记 -> 去重保留一条，计入 duplicate_dropped；
- 同 (specimen_code, measure_no) 异值 -> 整份数据冲突，抛 ValueError；
- 同一 specimen_code 跨处理格（温度/釉层不一致）-> 整份冲突，抛 ValueError；
- 同一试片的多个不同测次先做算术均值，分析时每片只贡献一个独立观测。
"""
from collections import OrderedDict
import numpy as np

ALLOWED_COLUMNS = {'specimen_code', 'temperature', 'glaze', 'strength_mpa', 'measure_no'}


def check_columns(fieldnames):
    unknown = [f for f in (fieldnames or []) if f is not None and f not in ALLOWED_COLUMNS]
    if unknown:
        raise ValueError(f'CSV包含未知列：{",".join(unknown)}；允许列：{",".join(sorted(ALLOWED_COLUMNS))}')
    missing = ALLOWED_COLUMNS - set(fieldnames or []) - {'measure_no'}
    if missing:
        raise ValueError(f'CSV缺少必需列：{",".join(sorted(missing))}')


def aggregate_specimens(rows):
    """返回 (aggregated_rows, audit)。

    rows: dict 列表，键含 specimen_code/temperature/glaze/strength_mpa，
          可选 measure_no（缺省视为 1）。
    aggregated_rows: 每试片一条，strength_mpa 为该试片各测次算术均值，
          另带 measure_count 与 raw_values。
    audit: {raw_count, duplicate_dropped, conflict_count 等计数与模式标记}
    """
    # 键 (specimen_code, measure_no) -> {'cell':(t,g),'value':float}
    measures = OrderedDict()
    # specimen_code -> (temperature, glaze)
    specimen_cell = {}
    duplicate_dropped = 0

    for idx, row in enumerate(rows, start=1):
        code = row['specimen_code']
        measure_no = int(row.get('measure_no', 1) or 1)
        value = float(row['strength_mpa'])
        cell = (row['temperature'], row['glaze'])

        if code in specimen_cell and specimen_cell[code] != cell:
            old_t, old_g = specimen_cell[code]
            raise ValueError(
                f'试片 {code} 跨处理格登记：({old_t},{old_g}) 与 ({cell[0]},{cell[1]})；'
                '同一试片必须属于同一处理格'
            )
        specimen_cell.setdefault(code, cell)

        key = (code, measure_no)
        if key in measures:
            seen = measures[key]
            if seen['cell'] != cell:
                raise ValueError(
                    f'试片 {code} 测次 {measure_no} 跨处理格登记：'
                    f'({seen["cell"][0]},{seen["cell"][1]}) 与 ({cell[0]},{cell[1]})'
                )
            if seen['value'] == value:
                duplicate_dropped += 1  # 完全同值的重复登记，去重
                continue
            raise ValueError(
                f'试片 {code} 测次 {measure_no} 存在不同读数：{seen["value"]} 与 {value}；'
                '同测次异值无法判定有效读数，整份拒收'
            )
        measures[key] = {'cell': cell, 'value': value}

    # 按试片归集（保持首次出现顺序，便于稳定排序与展示）
    grouped = OrderedDict()
    for (code, measure_no), item in measures.items():
        grouped.setdefault(code, []).append((measure_no, item['value'], item['cell']))

    aggregated = []
    repeated = False
    for code, entries in grouped.items():
        entries.sort(key=lambda e: e[0])
        temperature, glaze = entries[0][2]
        raw_values = [v for _, v, _ in entries]
        if len(raw_values) > 1:
            repeated = True
        aggregated.append({
            'specimen_code': code,
            'temperature': temperature,
            'glaze': glaze,
            'strength_mpa': float(np.mean(raw_values)),
            'measure_count': len(raw_values),
            'raw_values': raw_values,
            'measure_nos': [m for m, _, _ in entries],
        })

    audit = {
        'raw_count': len(rows),
        'deduped_count': len(measures),
        'specimen_count': len(aggregated),
        'duplicate_dropped': duplicate_dropped,
        'measure_mode': 'repeated' if repeated else 'single',
    }
    return aggregated, audit
