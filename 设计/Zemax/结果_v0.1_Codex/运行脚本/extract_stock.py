import json
from pathlib import Path
from zemax_mcp.server import zemax_lde_summary, zemax_set_wavelengths, zemax_operand

root = Path(r'F:\激光动态聚焦系统\Claude_Zemax任务审查')
out = root / '厂家原始模型'
out.mkdir(exist_ok=True)
names = ['LC1060-B', 'LC2265-B', 'LA1907-B', 'AC508-150-B',
         'AC254-150-B', 'LA1608-B', 'AC254-075-B', 'ACA254-075-B']
records = {}
for name in names:
    tool = TheSystem.Tools.OpenLensCatalogs()
    try:
        tool.SelectedVendor = 'THORLABS'
        tool.UseEFL = False
        tool.UseEPD = False
        tool.SetNumberOfElementsAny()
        tool.RunAndWaitForCompletion()
        item = next(tool.GetResult(i) for i in range(tool.MatchingLenses)
                    if tool.GetResult(i).LensName == name)
        item.LoadLens(False)
    finally:
        tool.Close()
    TheSystem.SaveAs(str(out / (name + '.zmx')))
    summary = zemax_lde_summary()
    zemax_set_wavelengths([.915])
    summary['efl_915_mm'] = zemax_operand('EFFL', [0, 1])
    summary['surface_details'] = []
    for i in range(TheSystem.LDE.NumberOfSurfaces):
        s = TheSystem.LDE.GetSurfaceAt(i)
        summary['surface_details'].append({'surf': i, 'mechanical_sd': s.MechanicalSemiDiameter,
                                          'aperture': str(s.ApertureData.CurrentType),
                                          'coating': s.Coating})
    records[name] = summary
    (root / '厂家镜片处方.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')

spot = TheSystem.Analyses.New_StandardSpot()
try:
    spot_settings = [n for n in dir(spot.GetSettings()) if not n.startswith('_')]
    spot_results = [n for n in dir(spot.GetResults()) if not n.startswith('_')]
finally:
    spot.Close()
wizard = TheSystem.MFE.SEQOptimizationWizard2
layout = TheSystem.Tools.Layouts.OpenCrossSectionExport()
try:
    layout_members = [n for n in dir(layout) if not n.startswith('_')]
finally:
    layout.Close()
meta = {'spot_settings': spot_settings, 'spot_results': spot_results,
        'wizard': [n for n in dir(wizard) if not n.startswith('_')], 'layout': layout_members,
        'lde': [n for n in dir(TheSystem.LDE) if not n.startswith('_')],
        'mce_cell': [n for n in dir(TheSystem.MCE.GetOperandAt(1).GetOperandCell(1)) if not n.startswith('_')]}
(root / 'API成员核验.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
result = {'lenses': len(records), 'output': str(root / '厂家镜片处方.json')}
