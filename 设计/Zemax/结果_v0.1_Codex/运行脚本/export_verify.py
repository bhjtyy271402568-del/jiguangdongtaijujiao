import json
import math
import re
import shutil
from pathlib import Path

from zemax_mcp.server import (zemax_layout_image, zemax_batch_ray_trace,
                            zemax_analysis_text, zemax_lde_summary)
from ZOSAPI.Analysis.Settings.Spot import IAS_Spot

OUT = Path(r'F:\激光动态聚焦系统\Zemax_915nm_1-10m_v0.1')
data = json.loads((OUT / '原始数据' / '计算结果.json').read_text(encoding='utf-8'))
S = TheSystem
MO = ZOSAPI.Editors.MFE.MeritOperandType
result_rows = []
checks = []
pupil = [[0., 0., ix / 20., iy / 20.] for ix in range(-20, 21) for iy in range(-20, 21) if ix*ix+iy*iy <= 400]

for model in data['ideal'] + data['real']:
    name = model['name']
    source = model.get('best', model)
    last = source['last_surface']
    gap_surf = source['gap_surface']
    rows = source['rows']
    for filename in model['files']:
        S.LoadFile(filename, False)
        assert S.MCE.NumberOfConfigurations == 5
        assert abs(S.SystemData.Wavelengths.GetWavelength(1).Wavelength - .915) < 1e-12
        assert S.SystemData.Wavelengths.NumberOfWavelengths == 1
        assert abs(S.SystemData.Aperture.ApertureValue - 4) < 1e-12
        for c, row in enumerate(rows, 1):
            S.MCE.SetCurrentConfiguration(c)
            gap = float(S.LDE.GetSurfaceAt(gap_surf).Thickness)
            length = float(S.LDE.GetSurfaceAt(last).Thickness)
            rms = float(S.MFE.GetOperandValue(MO.RSCE, 12, 1, 0., 0., 0., 0., 0., 0.))
            assert abs(gap - row['gap_mm']) < 1e-5, (name, c, gap, row['gap_mm'])
            assert abs(length - row['L_m'] * 1000) < 1e-8
            assert math.isfinite(rms)
            if 'rms_wfe_waves' in row:
                wave = float(S.MFE.GetOperandValue(MO.RWCE, 12, 1, 0., 0., 0., 0., 0., 0.))
                assert abs(wave - row['rms_wfe_12_rings']) < 1e-4, (name, c, wave, row['rms_wfe_12_rings'])
            checks.append({'file': filename, 'configuration': c, 'gap_mm': gap, 'L_mm': length, 'pass': True})
    for c in [1, 5]:
        S.LoadFile(model['files'][1], False)
        S.MCE.SetCurrentConfiguration(c)
        row = rows[c - 1]
        stem = name + '_' + str(int(row['L_m'])) + 'm'
        rays = zemax_batch_ray_trace(pupil)['rays']
        assert all(r['err'] == 0 and r['vignette'] == 0 for r in rays), stem
        fno = float(S.MFE.GetOperandValue(MO.WFNO, 0, 1, 0., 0., 0., 0., 0., 0.))
        analysis = S.Analyses.New_StandardSpot()
        try:
            settings = IAS_Spot(analysis.GetSettings())
            settings.Field.SetFieldNumber(1)
            settings.Wavelength.SetWavelengthNumber(1)
            settings.ReferTo = type(settings.ReferTo).Centroid
            settings.ShowAiryDisk = True
            settings.RayDensity = 25
            # Verified in OpticStudio 2024: 0=All, 1=Current, 2=Config 1, ...
            settings.Configuration = c + 1
            analysis.ApplyAndWaitForCompletion()
            result = analysis.GetResults()
            result.GetTextFile(str(OUT / '原始数据' / (stem + '_Zemax点列图.txt')))
            native_text = (OUT / '原始数据' / (stem + '_Zemax点列图.txt')).read_text(encoding='utf-16')
            assert re.search(r'结构\s+' + str(c) + r'\s+的\s+5', native_text), native_text[:500]
            native_rms = result.SpotData.GetRMSSpotSizeFor(1, 1)
            native_geo = result.SpotData.GetGeoSpotSizeFor(1, 1)
            settings.SaveTo(str(OUT / '原始数据' / (stem + '_Spot.CFG')))
        finally:
            analysis.Close()
        zernike = zemax_analysis_text('ZernikeStandardCoefficients', max_chars=20000)
        (OUT / '原始数据' / (stem + '_Zemax波前.txt')).write_text(zernike['text'], encoding='utf-8-sig')
        zernike_coeffs = {int(n): float(value) for n, value in re.findall(r'Z\s+(\d+)\s+([-+\d.Ee]+)\s*:', zernike['text'])}
        # Native graphics: whole propagation and separate magnified lens group.
        # Pin the current geometry into a temporary single configuration for export.
        S.MCE.MakeSingleConfigurationOpt(True)
        assert S.MCE.NumberOfConfigurations == 1
        assert abs(S.LDE.GetSurfaceAt(last).Thickness - row['L_m']*1000) < 1e-8
        layouts = []
        for suffix, end, stretch in [('全光路', last + 1, 8. if c == 1 else 60.), ('镜组放大', last, 1.)]:
            exported = zemax_layout_image(width=1600, height=800,
                settings={'StartSurface': 1, 'EndSurface': end, 'NumberOfRays': 9,
                          'Configuration': 1, 'Wavelength': 1, 'YStretch': stretch})
            dest = OUT / '图' / (stem + '_' + suffix + '.png')
            shutil.copy2(exported['path'], dest)
            assert dest.stat().st_size > 1000
            layouts.append(str(dest))
        result_rows.append({'name': name, 'configuration': c, 'L_m': row['L_m'],
                            'native_spot_rms_radius_um': float(native_rms),
                            'native_spot_geo_radius_um': float(native_geo),
                            'airy_radius_mm': 1.22 * .000915 * fno, 'working_fno': fno,
                            'zernike_waves': zernike_coeffs, 'rays': rays, 'layouts': layouts})
        (OUT / '原始数据' / '绘图数据.json').write_text(json.dumps(result_rows, ensure_ascii=False), encoding='utf-8')
    # Discard the temporary single-configuration copy; the saved five-config file is unchanged.
    S.LoadFile(model['files'][1], False)

(OUT / '原始数据' / '文件重开核验.json').write_text(json.dumps({'all_pass': True, 'checks': checks}, ensure_ascii=False, indent=2), encoding='utf-8')
result = {'reopen_checks': len(checks), 'models': 6, 'native_layouts': len(result_rows)*2,
          'spot_datasets': len(result_rows), 'ray_trace_checks': len(result_rows)*len(pupil), 'all_pass': True}
