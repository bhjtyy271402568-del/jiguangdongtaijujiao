"""Refine the one free air gap per configuration against Zemax RWCE, without changing stock glass."""
import copy
import json
import math
from pathlib import Path
from zemax_mcp.server import zemax_lde_summary, zemax_batch_ray_trace

OUT = Path(r'F:\激光动态聚焦系统\Zemax_915nm_1-10m_v0.1')
path = OUT / '原始数据' / '计算结果.json'
data = json.loads(path.read_text(encoding='utf-8'))
S = TheSystem
MO = ZOSAPI.Editors.MFE.MeritOperandType
def op(name, *args):
    v = list(args) + [0.]*(8-len(args))
    return float(S.MFE.GetOperandValue(getattr(MO, name), int(v[0]), int(v[1]), *v[2:]))

for model in data['real']:
    S.LoadFile(model['files'][0], False)
    previous = copy.deepcopy(model['best'])
    best = model['best']
    g = S.MCE.GetOperandAt(1)
    p = S.MCE.GetOperandAt(3)
    for c, row in enumerate(best['rows'], 1):
        S.MCE.SetCurrentConfiguration(c)
        gap_cell, pre_cell = g.GetOperandCell(c), p.GetOperandCell(c)
        initial = float(S.LDE.GetSurfaceAt(best['gap_surface']).Thickness)
        offset = initial + float(S.LDE.GetSurfaceAt(1).Thickness)
        samples = []
        def evaluate(gap):
            gap_cell.DoubleValue = gap
            pre_cell.DoubleValue = offset - gap
            value = op('RWCE', 12, 1)
            assert math.isfinite(value) and value >= 0
            samples.append((value, float(S.LDE.GetSurfaceAt(best['gap_surface']).Thickness)))
            return value
        before = evaluate(initial)
        left, right = initial - .5, initial + .5
        assert evaluate(left) > before and evaluate(right) > before
        ratio = (math.sqrt(5.) - 1.) / 2.
        x1, x2 = right - ratio*(right-left), left + ratio*(right-left)
        y1, y2 = evaluate(x1), evaluate(x2)
        for _ in range(40):
            if y1 < y2:
                right, x2, y2 = x2, x1, y1
                x1 = right - ratio*(right-left)
                y1 = evaluate(x1)
            else:
                left, x1, y1 = x1, x2, y2
                x2 = left + ratio*(right-left)
                y2 = evaluate(x2)
        _, optimal_gap = min(samples)
        after = evaluate(optimal_gap)
        assert after <= before + 1e-6, (model['name'], c, before, after)
        row.update(gap_mm=float(S.LDE.GetSurfaceAt(best['gap_surface']).Thickness),
                   rms_wfe_waves=after, rms_wfe_12_rings=after, rms_wfe_8_rings=op('RWCE', 8, 1),
                   rms_geo_radius_mm=op('RSCE', 12, 1), working_fno=op('WFNO', 0, 1),
                   positive_first_beam_diameter_mm=2*abs(op('REAY', best['gap_surface']+1, 1, 0, 0, 0, 1)))
        row['refinement_samples'] = len(samples)
        edge = zemax_batch_ray_trace([[0, 0, x, y] for x, y in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]])['rays']
        assert all(not r['err'] and not r['vignette'] for r in edge)
    best['travel_mm'] = max(r['gap_mm'] for r in best['rows']) - min(r['gap_mm'] for r in best['rows'])
    best['worst_wfe_waves'] = max(r['rms_wfe_waves'] for r in best['rows'])
    best['refinement'] = 'Native all-configuration DLS followed by independent scalar golden-section air-gap refinement using Zemax RWCE (12 rings); prescriptions fixed.'
    best['files'] = model['files']
    model['pre_refinement_best'] = previous
    S.MCE.SetCurrentConfiguration(1)
    for filename in model['files']:
        S.SaveAs(filename)
    model['prescription'] = zemax_lde_summary()
path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
result = [{'name': x['name'], 'travel_mm': x['best']['travel_mm'], 'worst_wfe': x['best']['worst_wfe_waves']} for x in data['real']]
