import json
import math
from pathlib import Path
from zemax_mcp.server import zemax_optimize, zemax_batch_ray_trace

OUT = Path(r'F:\激光动态聚焦系统\Zemax_915nm_1-10m_v0.1')
data = json.loads((OUT / '原始数据' / '计算结果.json').read_text(encoding='utf-8'))
S = TheSystem
MO = ZOSAPI.Editors.MFE.MeritOperandType

def op(name, *args):
    v = list(args) + [0.] * (8-len(args))
    return float(S.MFE.GetOperandValue(getattr(MO, name), int(v[0]), int(v[1]), *v[2:]))

gaussian = []
for model in data['ideal']:
    S.LoadFile(model['files'][0], False)
    for c, row in enumerate(model['rows'], 1):
        S.MCE.SetCurrentConfiguration(c)
        for m2 in [1., 3., 5., 8., 9., 10.]:
            embedded_waist = 2. / math.sqrt(m2)
            input_radius = op('GBPS', 1, 1, 0, embedded_waist, 0, m2)
            radius = op('GBPS', 4, 1, 0, embedded_waist, 0, m2)
            assert abs(input_radius - 2.) < 1e-8, (m2, input_radius)
            assert math.isfinite(radius) and radius > 0
            gaussian.append({'name': model['name'], 'configuration': c, 'L_m': row['L_m'], 'M2': m2,
                             'input_physical_diameter_mm': 2*input_radius, 'embedded_waist_radius_mm': embedded_waist,
                             'target_diameter_mm': 2*radius, 'definition': 'unclipped M2 equivalent Gaussian, no real-lens aberrations'})
(OUT / '原始数据' / '高斯光束条件评估.json').write_text(json.dumps(gaussian, ensure_ascii=False, indent=2), encoding='utf-8')

dense = []
for model in [data['real'][1], data['real'][3]]:
    S.LoadFile(model['files'][0], False)
    gap_row = S.MCE.GetOperandAt(1)
    L_row = S.MCE.GetOperandAt(2)
    pre_row = S.MCE.GetOperandAt(3)
    gap_cell = gap_row.GetOperandCell(1)
    pre_offset = gap_cell.DoubleValue + pre_row.GetOperandCell(1).DoubleValue
    gap_cell.MakeSolveVariable()
    for k in range(19):
        L = 1000. + k*500.
        L_row.GetOperandCell(1).DoubleValue = L
        S.MCE.SetCurrentConfiguration(1)
        zemax_optimize(cores=4, cycles=0)
        pre_row.GetOperandCell(1).DoubleValue = pre_offset - gap_cell.DoubleValue
        wave = op('RWCE', 12, 1)
        rays = zemax_batch_ray_trace([[0.,0.,0.,-1.], [0.,0.,0.,0.], [0.,0.,0.,1.]])['rays']
        assert all(not r['err'] and not r['vignette'] for r in rays)
        dense.append({'name': model['name'], 'L_m': L/1000, 'gap_mm': gap_cell.DoubleValue,
                      'rms_wfe_waves': wave, 'rms_geo_radius_mm': op('RSCE', 12, 1), 'trace_pass': True})
(OUT / '原始数据' / '双胶合_每0.5m复核.json').write_text(json.dumps(dense, ensure_ascii=False, indent=2), encoding='utf-8')
result = {'gaussian_cases': len(gaussian), 'dense_cases': len(dense), 'm2_at_10m': [r for r in gaussian if r['L_m']==10],
          'note': 'Source files not overwritten. Gaussian result conditional on 4mm physical input diameter; clipped/aberrated real laser not qualified.'}
