"""MCP job: ideal checks and four stock-lens orientation comparisons at 915 nm."""
import copy
import json
import math
import re
from pathlib import Path

from zemax_mcp.server import (zemax_new_system, zemax_set_aperture, zemax_set_wavelengths,
    zemax_set_fields, zemax_lde_set_surface, zemax_lde_summary,
    zemax_merit_wizard, zemax_optimize, zemax_operand, zemax_batch_ray_trace)

ROOT = Path(r'F:\激光动态聚焦系统\Claude_Zemax任务审查')
OUT = ROOT.parent / 'Zemax_915nm_1-10m_v0.1'
MODELS = OUT / '模型'
for path in [OUT, MODELS, OUT / '原始数据', OUT / '图']:
    path.mkdir(exist_ok=True)
stock = json.loads((ROOT / '厂家镜片处方.json').read_text(encoding='utf-8'))
distances = [1000., 2000., 3000., 5000., 10000.]
S = TheSystem
MO = ZOSAPI.Editors.MFE.MeritOperandType
report = {'wavelength_um': .915, 'entrance_pupil_mm': 4, 'beam_model': 'collimated uniform circular pupil, provisional',
          'positive_last_vertex_fixed': True, 'ideal': [], 'real': []}


def op(name, *args):
    values = list(args) + [0.] * (8 - len(args))
    return float(S.MFE.GetOperandValue(getattr(MO, name), int(values[0]), int(values[1]), *values[2:]))


def base(title):
    zemax_new_system()
    S.SystemData.Units.LensUnits = type(S.SystemData.Units.LensUnits).Millimeters
    S.SystemData.TitleNotes.Title = title
    S.SystemData.TitleNotes.Notes = '915nm; provisional 4mm collimated uniform pupil. Not a measured laser qualification.'
    zemax_set_aperture(value=4)
    zemax_set_wavelengths([.915])
    zemax_set_fields('Angle', [[0., 0.]])
    S.SystemData.MaterialCatalogs.AddCatalog('SCHOTT')
    S.LDE.GetSurfaceAt(1).Comment = 'Input pupil 4mm provisional'


def configs(gap_surf, last_surf, gaps, lengths):
    mce = S.MCE
    for _ in lengths[1:]:
        mce.AddConfiguration(False)
    gap_row = mce.GetOperandAt(1)
    gap_row.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.THIC)
    gap_row.Param1 = gap_surf
    length_row = mce.AddOperand()
    length_row.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.THIC)
    length_row.Param1 = last_surf
    for i, (gap, length) in enumerate(zip(gaps, lengths), 1):
        gap_row.GetOperandCell(i).DoubleValue = gap
        length_row.GetOperandCell(i).DoubleValue = length
    mce.SetCurrentConfiguration(1)
    return gap_row


def pickup(gap_surf, offset):
    # Explicit configuration values also make the translating negative lens easy to inspect.
    row = S.MCE.AddOperand()
    row.ChangeType(ZOSAPI.Editors.MCE.MultiConfigOperandType.THIC)
    row.Param1 = 1
    for c in range(1, 6):
        gap = S.MCE.GetOperandAt(1).GetOperandCell(c).DoubleValue
        row.GetOperandCell(c).DoubleValue = offset - gap
    return row


def fixed_z(last_surf):
    return sum(float(S.LDE.GetSurfaceAt(i).Thickness) for i in range(1, last_surf))


def save(name):
    S.MCE.SetCurrentConfiguration(1)
    folder = MODELS / '朝向比较' if re.search(r'_N[01]P[01]$', name) else MODELS
    folder.mkdir(exist_ok=True)
    paths = []
    for suffix in ['.zmx', '.zos']:
        path = folder / (name + suffix)
        S.SaveAs(str(path))
        assert path.exists() and path.stat().st_size > 100
        paths.append(str(path))
    return paths


def flush():
    (OUT / '原始数据' / '计算结果.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


for label, f1, f2, reference in [('01_理想长焦', -30., 150., 180.), ('02_理想短焦', -15., 75., 100.)]:
    base(label)
    S.LDE.InsertNewSurfaceAt(2)
    S.LDE.InsertNewSurfaceAt(2)
    zemax_lde_set_surface(2, surface_type='Paraxial', params={'1': f1}, comment='Moving negative ideal lens')
    zemax_lde_set_surface(3, surface_type='Paraxial', params={'1': f2}, comment='Fixed positive ideal lens')
    gaps = [f2 * L / (L - f2) + f1 for L in distances]
    configs(2, 3, gaps, distances)
    pickup(2, reference)
    rows = []
    for i, L in enumerate(distances, 1):
        S.MCE.SetCurrentConfiguration(i)
        rms = op('RSCE', 8, 1)
        zpos = fixed_z(3)
        assert math.isfinite(rms) and rms < 1e-6
        assert abs(zpos - reference) < 1e-5, (zpos, reference, zemax_lde_summary())
        rows.append({'configuration': i, 'L_m': L / 1000, 'gap_mm': S.LDE.GetSurfaceAt(2).Thickness,
                     'rms_geo_radius_mm': rms, 'positive_vertex_z_mm': zpos,
                     'positive_beam_diameter_mm': 2 * abs(op('REAY', 3, 1, 0, 0, 0, 1)),
                     'working_fno': op('WFNO', 0, 1)})
    paths = save(label)
    report['ideal'].append({'name': label, 'f1_mm': f1, 'f2_mm': f2, 'travel_mm': max(gaps) - min(gaps),
                            'rows': rows, 'files': paths, 'last_surface': 3, 'gap_surface': 2})
    flush()


def lens_faces(name, reverse):
    original = stock[name]['surfaces'][1:-1]
    assert all(row['type'] == '标准面' and row['conic'] == 0 for row in original)
    faces = []
    indexes = range(len(original) - 1, -1, -1) if reverse else range(len(original))
    for idx in indexes:
        row = original[idx]
        radius = float(row['radius'])
        material = original[idx - 1]['material'] if reverse and idx > 0 else ('' if reverse else row['material'])
        thickness = original[idx - 1]['thickness'] if reverse and idx > 0 else (0. if reverse else row['thickness'])
        faces.append({'radius': -radius if reverse else radius, 'thickness': thickness,
                      'material': material, 'semi_diameter': row['semi_dia'],
                      'coating': stock[name]['surface_details'][idx + 1]['coating']})
    faces[-1]['thickness'] = 0.
    return faces


def build_real(name, neg, pos, flip_neg, flip_pos, f1, f2, ref):
    base(name)
    a = lens_faces(neg, flip_neg)
    b = lens_faces(pos, flip_pos)
    faces = a + b
    for _ in faces:
        S.LDE.InsertNewSurfaceAt(S.LDE.NumberOfSurfaces - 1)
    for i, face in enumerate(faces, 2):
        face = dict(face)
        coating = face.pop('coating')
        zemax_lde_set_surface(i, **face)
        surface = S.LDE.GetSurfaceAt(i)
        surface.Comment = (neg if i < 2 + len(a) else pos) + (' rev' if (flip_neg if i < 2 + len(a) else flip_pos) else '')
        surface.Coating = coating
        # Conservative guaranteed clear aperture: 90% of physical diameter.
        aperture = surface.ApertureData.CreateApertureTypeSettings(ZOSAPI.Editors.LDE.SurfaceApertureTypes.CircularAperture)
        aperture._S_CircularAperture.MinimumRadius = 0.
        aperture._S_CircularAperture.MaximumRadius = .9 * face['semi_diameter']
        surface.ApertureData.ChangeApertureTypeSettings(aperture)
        surface.MechanicalSemiDiameter = face['semi_diameter']
    gap_surface = 1 + len(a)
    last_surface = 1 + len(faces)
    glass_track = sum(face['thickness'] for face in faces)
    gaps = [f2 * L / (L - f2) + f1 - glass_track / 2 for L in distances]
    gap_row = configs(gap_surface, last_surface, gaps, distances)
    pre_row = pickup(gap_surface, ref - glass_track)
    for c in range(1, 6):
        gap_row.GetOperandCell(c).MakeSolveVariable()
    return gap_surface, last_surface, gap_row, pre_row, ref - glass_track


schemes = [('03_长焦_平凸', 'LC1060-B', 'LA1907-B', -30., 150., 180.),
           ('04_长焦_双胶合', 'LC1060-B', 'AC508-150-B', -30., 150., 180.),
           ('05_短焦_平凸', 'LC2265-B', 'LA1608-B', -15., 75., 100.),
           ('06_短焦_双胶合', 'LC2265-B', 'AC254-075-B', -15., 75., 100.)]
for name, neg, pos, f1, f2, reference in schemes:
    candidates = []
    for flip_neg, flip_pos in [(False, False), (False, True), (True, False), (True, True)]:
        gap_s, last_s, gap_row, pre_row, pre_offset = build_real(name, neg, pos, flip_neg, flip_pos, f1, f2, reference)
        settings = {'Type': 'RMS', 'Criterion': 'Wavefront', 'Reference': 'Centroid',
                    'UseAllConfigurations': True, 'UseAllFields': True, 'UseGaussianQuadrature': True,
                    'Rings': 8, 'Arms': 'Arms_8', 'UseGlassBoundaryValues': False,
                    'UseAirBoundaryValues': False, 'StartAt': 1}
        zemax_merit_wizard(settings)
        optimized = zemax_optimize(cores=4, cycles=0)
        for c in range(1, 6):
            gap_cell = gap_row.GetOperandCell(c)
            pre_row.GetOperandCell(c).DoubleValue = pre_offset - gap_cell.DoubleValue
            gap_cell.MakeSolveFixed()
        rows = []
        for c, L in enumerate(distances, 1):
            S.MCE.SetCurrentConfiguration(c)
            gap = S.LDE.GetSurfaceAt(gap_s).Thickness
            wave = op('RWCE', 8, 1)
            wave_check = op('RWCE', 12, 1)
            assert all(math.isfinite(x) for x in [gap, wave, wave_check])
            assert gap > 0 and abs(S.LDE.GetSurfaceAt(last_s).Thickness - L) < 1e-8
            assert abs(fixed_z(last_s) - reference) < 1e-5
            rays = zemax_batch_ray_trace([[0, 0, x, y] for x, y in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]])['rays']
            rows.append({'configuration': c, 'L_m': L / 1000, 'gap_mm': gap,
                         'rms_wfe_waves': wave, 'rms_wfe_12_rings': wave_check,
                         'rms_geo_radius_mm': op('RSCE', 8, 1), 'working_fno': op('WFNO', 0, 1),
                         'positive_first_beam_diameter_mm': 2 * abs(op('REAY', gap_s + 1, 1, 0, 0, 0, 1)),
                         'positive_last_vertex_z_mm': fixed_z(last_s),
                         'edge_ray_errors': sum(bool(r['err']) for r in rays),
                         'edge_vignetted': sum(bool(r['vignette']) for r in rays)})
        gaps = [r['gap_mm'] for r in rows]
        candidate = {'flip_negative': flip_neg, 'flip_positive': flip_pos, 'rows': rows,
                     'worst_wfe_waves': max(r['rms_wfe_waves'] for r in rows),
                     'travel_mm': max(gaps) - min(gaps), 'optimization': optimized,
                     'gap_surface': gap_s, 'last_surface': last_s}
        orient_name = name + '_N' + str(int(flip_neg)) + 'P' + str(int(flip_pos))
        candidate['files'] = save(orient_name)
        candidates.append(candidate)
        # Persist each completed orientation even if a later operation fails.
        (OUT / '原始数据' / (orient_name + '.json')).write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding='utf-8')
    valid = [c for c in candidates if all(r['edge_ray_errors'] == 0 and r['edge_vignetted'] == 0 for r in c['rows'])]
    best = min(valid or candidates, key=lambda c: c['worst_wfe_waves'])
    S.LoadFile(best['files'][0], False)
    best_files = save(name)
    report['real'].append({'name': name, 'negative': neg, 'positive': pos,
                           'negative_efl_915': stock[neg]['efl_915_mm']['value'],
                           'positive_efl_915': stock[pos]['efl_915_mm']['value'],
                           'orientations': candidates, 'best': best, 'files': best_files,
                           'prescription': zemax_lde_summary()})
    flush()

result = {'output': str(OUT), 'ideal': [{'name': x['name'], 'travel_mm': x['travel_mm']} for x in report['ideal']],
          'real': [{'name': x['name'], 'travel_mm': x['best']['travel_mm'], 'wfe_max': x['best']['worst_wfe_waves'],
                    'flips': [x['best']['flip_negative'], x['best']['flip_positive']]} for x in report['real']]}
