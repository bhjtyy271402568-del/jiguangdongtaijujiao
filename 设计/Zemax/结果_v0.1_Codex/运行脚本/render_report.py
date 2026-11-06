"""Create a local illustrated report from the saved OpticStudio results."""
import html
import json
import math
import re
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np

OUT = Path(r'F:\激光动态聚焦系统\Zemax_915nm_1-10m_v0.1')
DATA = OUT / '原始数据'
FIG = OUT / '图'
data = json.loads((DATA / '计算结果.json').read_text(encoding='utf-8'))
spots = json.loads((DATA / '绘图数据.json').read_text(encoding='utf-8'))
gaussian = json.loads((DATA / '高斯光束条件评估.json').read_text(encoding='utf-8'))
dense = json.loads((DATA / '双胶合_每0.5m复核.json').read_text(encoding='utf-8'))
checks = json.loads((DATA / '文件重开核验.json').read_text(encoding='utf-8'))
assert len(spots) == 12 and len(checks['checks']) == 60 and checks['all_pass']
plt.rcParams.update({'font.family': FontProperties(fname=r'C:\Windows\Fonts\msyh.ttc').get_name(),
                     'axes.unicode_minus': False, 'axes.spines.top': False, 'axes.spines.right': False,
                     'font.size': 10, 'axes.titlesize': 12, 'figure.facecolor': 'white'})
colors = ['#8e647b', '#326da8', '#b87332', '#168878']

def savefig(fig, name):
    fig.savefig(FIG / (name + '.png'), dpi=180, bbox_inches='tight')
    fig.savefig(FIG / (name + '.svg'), bbox_inches='tight')
    plt.close(fig)

for model in data['ideal'] + data['real']:
    pair = [s for s in spots if s['name'] == model['name']]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 5.2))
    for ax, spot in zip(axes, pair):
        xy = np.array([[r['x'], r['y']] for r in spot['rays']])
        xy -= xy.mean(axis=0)
        ax.scatter(xy[:, 0], xy[:, 1], s=2.5, color='#217a9a', alpha=.65, label='Zemax 几何光线落点')
        a = spot['airy_radius_mm']
        ax.add_patch(plt.Circle((0, 0), a, fill=False, ec='#ca7629', lw=1.5, label='艾里斑第一暗环'))
        extent = max(float(np.abs(xy).max()), a) * 1.18
        ax.set(xlim=(-extent, extent), ylim=(-extent, extent), aspect='equal', xlabel='X / mm', ylabel='Y / mm')
        ax.set_title(f"{spot['L_m']:g} m · 艾里斑直径 {2*a:.3f} mm")
        ax.grid(alpha=.18)
        ax.text(.02, .02, f"原生点列图 RMS 半径：{spot['native_spot_rms_radius_um']/1000:.4g} mm\n"
                f"原生点列图最大半径：{spot['native_spot_geo_radius_um']/1000:.4g} mm",
                transform=ax.transAxes, fontsize=9, va='bottom', bbox={'facecolor':'white', 'edgecolor':'none', 'alpha':.9})
    axes[0].legend(loc='upper left', fontsize=8)
    fig.suptitle(model['name'][3:] + '｜点列图与衍射尺度', fontsize=16)
    fig.text(.5, .01, 'MCP 光线数据重绘，并非软件截图；两图坐标尺度不同。几何点列图不等于实际激光强度光斑。', ha='center', fontsize=9, color='#555')
    fig.tight_layout(rect=(0,.055,1,.95))
    savefig(fig, model['name'] + '_点列图')

fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
for model, color in zip(data['real'], colors):
    rows = model['best']['rows']
    axes[0].plot([r['L_m'] for r in rows], [r['rms_wfe_waves'] for r in rows], 'o-', color=color, label=model['name'][3:])
    axes[1].plot([r['L_m'] for r in rows], [r['gap_mm'] for r in rows], 'o-', color=color, label=model['name'][3:])
axes[0].axhline(.07, color='#b24a49', ls='--', lw=1, label='0.07 波参考标准')
axes[0].set(yscale='log', xlabel='工作距离 / m', ylabel='RMS 波前 / waves', title='真实镜组：五个设计配置')
axes[1].set(xlabel='工作距离 / m', ylabel='镜间空气隙 / mm', title='负镜后顶点 → 正镜前顶点')
for ax in axes:
    ax.grid(alpha=.18)
    ax.legend(fontsize=8)
fig.tight_layout()
savefig(fig, '真实方案比较')

fig, ax = plt.subplots(figsize=(8.8, 4.2))
for name, style in [('01_理想长焦', 'o--'), ('02_理想短焦', 's-')]:
    rows = [r for r in gaussian if r['name'] == name and r['L_m'] == 10]
    ax.plot([r['M2'] for r in rows], [r['target_diameter_mm'] for r in rows], style, label=name[3:])
ax.axhline(5, color='#ad4b4b', ls='--', label='5 mm 目标')
ax.set(xlabel='假定光束质量 M²', ylabel='10 m 处等效高斯直径 / mm', title='同样是 4 mm 入射光束，M² 会改变结果')
ax.grid(alpha=.18)
ax.legend()
fig.text(.5, -.02, 'Zemax GBPS 计算；固定物理入射直径，嵌入高斯腰斑半径 = 2 / √M² mm。忽略截光和真实镜片像差。', ha='center', fontsize=9)
fig.tight_layout()
savefig(fig, 'M2条件评估')

def esc(x):
    return html.escape(str(x))

def table(headers, rows):
    return '<div class="scroll"><table><thead><tr>' + ''.join('<th>'+h+'</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows) + '</tbody></table></div>'

def picture(name, caption):
    return f'<figure><a href="图/{name}"><img loading="lazy" src="图/{name}" alt="{esc(caption)}"></a><figcaption>{caption}</figcaption></figure>'

short = data['real'][3]
long = data['real'][1]
short_best, long_best = short['best'], long['best']
short_ratio = abs(short['positive_efl_915'] / short['negative_efl_915'])
reduction = 100 * (1 - short_best['worst_wfe_waves']/data['real'][2]['best']['worst_wfe_waves'])

intro = f'''<p class="eyebrow">OPTICSTUDIO 2024 R1 · MCP 实际运行 · 2026-11-06</p>
<h1>915 nm 调焦镜组<br>首轮结果与操作复盘</h1>
<p class="lead">理想模型通过；真实镜组有明确取舍。<strong>现阶段还不能证明实际激光在 1–10 m 全程达到 ≤5 mm。</strong></p>
<div class="cards"><div><b>{short_best['travel_mm']:.2f} mm</b><span>短焦双胶合 · 调焦行程</span></div><div><b>{long_best['travel_mm']:.2f} mm</b><span>长焦双胶合 · 调焦行程</span></div><div><b>4 mm / M² 待确认</b><span>决定真实光斑的剩余输入</span></div></div>
<p>若继续围绕现有短行程主体研究，优先看<strong>06_短焦_双胶合</strong>。它比短焦平凸的最差波前降低约 {reduction:.1f}%，但 1 m 处仍有 {short_best['worst_wfe_waves']:.3f} 波，未达到任务说明的 0.07 波标准。
长焦双胶合五个设计点均小于 0.07 波，但需要约 {long_best['travel_mm']:.2f} mm 行程，且本轮物镜为 Ø50.8 mm，需重新考虑结构。</p>
<div class="links"><a href="模型/06_短焦_双胶合.zos">打开短焦双胶合模型</a><a href="模型/01_理想长焦.zos">从理想模型开始学</a><a href="#how">看操作步骤</a><a href="审查反馈与结论.txt">纯文字结论</a></div>
<p class="note">模型是可行性研究文件，非已定型镜片设计。工作距离已正式改为 1–10 m；915 nm 已确认；4 mm 入射直径暂用；≤5 mm 是用户给定的评估目标，直径定义仍待明确。</p>'''

summary_rows = []
for model in data['real']:
    b = model['best']
    summary_rows.append([model['name'][3:], esc(model['negative'])+'<br>'+esc(model['positive']),
        f'{b["travel_mm"]:.3f}', f'{b["worst_wfe_waves"]:.4f}',
        '五点满足' if b['worst_wfe_waves']<=.07 else '有点不满足',
        f'<a href="模型/{model["name"]}.zos">.zos</a> · <a href="模型/{model["name"]}.zmx">.zmx</a>'])
main = '<h2 id="results">1. 哪个方案值得继续</h2>' + table(['真实镜组','Thorlabs 型号<br>负镜 / 正镜','行程 / mm','最差 RMS 波前 / 波','≤0.07 波','模型'],summary_rows)
main += '<p>本表的“通过”仅针对五个设计点的镜片波前质量，不能当作实际激光光斑 ≤5 mm 的证明。短焦平凸在 10 m 的几何扩散已经很大，不适合作为本轮首选。</p>'
main += picture('真实方案比较.png', '圆点是 1、2、3、5、10 m 的真实 Zemax 结果；连线仅帮助比较，并非控制卡插值表。')
main += '<p>双胶合方案另做了每隔 0.5 m 的独立调焦检查，共 38 个点。短焦方案的主要波前问题集中在近端，1.5 m 检查点已低于 0.07 波。此离散检查不能替代连续全范围的严格证明或装调容差分析。</p>'
main += '<h3>机械上要记住的两件事</h3><p>当前 v0.9 装配的已核验运动范围是 −7.8～+3.8 mm，即 <b>11.6 mm</b>，不是 Claude 文档写的 8 mm。短焦方案的行程能放进这个范围；但镜片的基准位置必须重新安排。真实短焦双胶合镜间空气隙约 53–59 mm，原 CAD 两镜中心占位约 120 mm，不能仅换镜片就直接使用。</p>'
main += '<p>表中 d 是<strong>负镜最后一面顶点到正镜第一面顶点的空气距离</strong>，不是两镜片中心距，也不是主平面距离。工作距离 L 从正镜最后一面顶点量到目标面。CAD 镜座尺寸必须用真实厚度和镜片安装基准换算。</p>'

models_html = '<h2>2. 每个配置的数值</h2><p>下面 RMS 光斑是<strong>几何半径</strong>，单位 mm；不能直接与“实际光斑直径 ≤5 mm”混用。真实方案的波前与几何 RMS 使用 12 环高斯求积读取。文件保留了全部五个配置。</p>'
for model in data['ideal']:
    models_html += f'<details><summary>{model["name"]}：行程 {model["travel_mm"]:.6f} mm</summary>'
    models_html += table(['距离 / m','薄透镜间距 / mm','几何 RMS 半径 / mm','正镜处光束直径 / mm'],
       [[f'{r["L_m"]:g}',f'{r["gap_mm"]:.6f}',f'{r["rms_geo_radius_mm"]:.3g}',f'{r["positive_beam_diameter_mm"]:.3f}'] for r in model['rows']])
    models_html += picture(model['name']+'_点列图.png','理想模型：几何点几乎重合，艾里斑仍有有限大小。') + '</details>'
for model in data['real']:
    b = model['best']
    models_html += f'<details {"open" if model==short else ""}><summary>{model["name"]}：行程 {b["travel_mm"]:.6f} mm</summary>'
    models_html += table(['距离 / m','镜间空气隙 / mm','RMS 波前 / 波','几何 RMS 半径 / mm','正镜首面处光束直径 / mm'],
       [[f'{r["L_m"]:g}',f'{r["gap_mm"]:.6f}',f'{r["rms_wfe_waves"]:.6f}',f'{r["rms_geo_radius_mm"]:.6f}',f'{r["positive_first_beam_diameter_mm"]:.3f}'] for r in b['rows']])
    models_html += f'<p>915 nm 实际焦距：负镜 {model["negative_efl_915"]:.4f} mm；正镜 {model["positive_efl_915"]:.4f} mm；焦距绝对值比 {abs(model["positive_efl_915"]/model["negative_efl_915"]):.4f}。</p>'
    models_html += '<p>选中朝向：负镜' + ('平面朝入射' if b['flip_negative'] else '凹面朝入射') + '；正镜相对厂家原处方反向放置。具体面形见下方原生光路图。</p>'
    models_html += picture(model['name']+'_点列图.png','数据图：光线落点来自 Zemax Batch Ray Trace；橙圈按 Zemax 工作 F 数计算艾里斑。文字统计来自原生 Standard Spot Diagram，采样方式与求积 RMS 略有差异。')
    models_html += '<div class="two">'+picture(model['name']+'_1m_镜组放大.png','1 m 配置：Zemax 原生镜组光路图。')+picture(model['name']+'_10m_镜组放大.png','10 m 配置：Zemax 原生镜组光路图。')+'</div>'
    models_html += picture(model['name']+'_10m_全光路.png','10 m 全光路：纵向尺寸放大 60 倍，以便看到光束；不要用此图量结构比例。')
    models_html += '</details>'

beam = '<h2>3. 为什么还不能判定实际光斑达标</h2>'
beam += '<p>几何点列图检查光线落点，波前检查镜片像差；它们都没有自动给定真实激光器的 M²、束腰位置或强度分布。额外做的高斯模型固定物理输入直径为 4 mm，假定入射参考面处是腰斑，考察 M² 变化；这与前面的均匀圆瞳几何模型是两种条件模型。</p>'
beam += picture('M2条件评估.png','数值由 Zemax GBPS 操作数计算，不是激光器实测值。')
beam += table(['M² 假设','理想长焦 10 m 直径 / mm','理想短焦 10 m 直径 / mm'], [[f'{m:g}']+[f'{next(r["target_diameter_mm"] for r in gaussian if r["name"]==n and r["M2"]==m and r["L_m"]==10):.3f}' for n in ['01_理想长焦','02_理想短焦']] for m in [1,3,5,8,9,10]])
beam += '<p>当前条件下，M² 到约 9 时，理想模型在 10 m 已超过 5 mm。实际设计还要加入镜片像差、孔径截断和装调误差；不能把这张表视为整机合格证，也不能把几个不同定义的直径直接相加。</p>'
beam += f'<p>另外，“5 倍”目前是名义目标。真实短焦候选在 915 nm 的焦距比约 <b>{short_ratio:.4f}</b>，并非精确 5.000。若严格要求 5.000，需要重新配焦距。有限距离聚焦时，正镜各面上的光束直径也会变化，不能固定按 20 mm 处理。</p>'
beam += '<p class="note">后续需要：准直后束径及其定义、M²（必要时 X/Y 分别给出）、束腰位置或发散角；并明确“5 mm”指 1/e²、D4σ、FWHM，还是某个包围能量直径。单色像差通过也没有验证功率承受、镀膜损伤或热效应。</p>'
beam += '<p>高斯半径与嵌入光束的定义见 <a href="https://ansyshelp.ansys.com/public/Views/Secured/Zemax/v251/en/OpticStudio_User_Guide/OpticStudio_Help/topics/Paraxial_Gaussian_Beam.html">Ansys：Paraxial Gaussian Beam</a>。</p>'

how = '''<h2 id="how">4. 明早照着做：先看懂，再试改一个数</h2>
<ol class="steps">
<li><b>打开一个模型。</b>启动 Zemax，按 <kbd>Ctrl+O</kbd>，选本包“模型”中的 <code>06_短焦_双胶合.zos</code>。学习薄透镜时选 <code>01_理想长焦.zos</code>。同名 .zmx 是文本格式备份。</li>
<li><b>看镜头数据表。</b>按 <kbd>Shift+F1</kbd> 打开 Lens Data Editor。真实短焦模型中，面 2～3 是负镜；面 4～6 是双胶合正镜；面 7 是目标。Thickness 表示“这一面到下一面”的轴向距离，Material 是该面之后的介质。</li>
<li><b>切换距离。</b>按 <kbd>F7</kbd> 打开 Multi-Configuration Editor，双击配置列头。配置 1、2、3、4、5 分别对应 1、2、3、5、10 m。<kbd>Ctrl+A</kbd> 切下一个配置。选中一个单元格不等于切换当前配置。</li>
<li><b>看光路。</b>按 <kbd>Ctrl+L</kbd> 打开 Cross-Section。切换配置后按 <kbd>Ctrl+Shift+U</kbd> 更新所有窗口。镜片较小时，把鼠标放在镜片区域左上方，按住左键约半秒，等指针变成十字后向右下拖框，框住两组镜片，松开即可放大。右键选择 Reset Zoom（重置缩放）可恢复全图。操作见 <a href="https://ansyshelp.ansys.com/public/Views/Secured/Zemax/v25101/en/OpticStudio_User_Guide/OpticStudio_Help/topics/Using_Pan_and_Zoom.html">官方缩放说明</a>。</li>
<li><b>看点列图。</b>按 <kbd>Ctrl+Shift+S</kbd> 打开 Standard Spot Diagram。Settings 中选 Configuration=Current、Field=1、Wavelength=1，勾 Show Airy Disk，Reference=Centroid。切换配置并更新。RMS Radius 是半径；橙圈/艾里圈是衍射尺度，不是完整真实激光光斑。</li>
<li><b>看波前。</b>Analyze 中打开 Wavefront / Zernike Standard Coefficients，选单一波长 0.915 μm 和当前配置。在 Text 页查看 RMS 与各项系数。Z11 是初级球差项；本轮的主要残余像差是轴上球差。斯特列尔率 (Est) 是估算，不是实测 PSF。</li>
</ol>
<h3>真实短焦模型里，F7 的三行分别是什么</h3>'''
how += table(['MCE 行','作用','说明'],[['THIC 3','镜间空气隙 d','这是本次求出的调焦量'],['THIC 6','工作距离 L','1000 / 2000 / 3000 / 5000 / 10000 mm'],['THIC 1','入瞳到负镜的空气段','与 d 反向变化，让正镜保持在固定坐标']])
how += '''<p>演示中把短焦正镜最后顶点放在 z=100 mm、长焦放在 z=180 mm，仅用于固定坐标参考；这两个数不是要求你照做的 CAD 尺寸。真实短焦的关系是 <code>THIC 1 + THIC 3 + 3.0 + 1.6 + 5.0 = 100 mm</code>。</p>
<h3>我这次是怎样优化的</h3>
<p>先在厂家目录选入镜片，保持曲率、玻璃、中心厚度不变；负镜和正镜各试正反两种方向，共四种组合。每个组合建立五个距离配置，只把镜间空气隙作为变量。用 RMS Wavefront / Centroid 的多配置评价函数跑 Zemax DLS，选取最差波前较小且没有截光的朝向；然后逐配置细化空气隙，评价值仍取 Zemax RWCE。最后补回负镜前方空气段并冻结变量，便于你查看。</p>
<p>自己练习时，先“另存为”。F7 里对 THIC 3 的五个数按 <kbd>Ctrl+Z</kbd> 设为变量；这在 Zemax 是“设变量”，<strong>不是撤销</strong>。F6 打开评价函数编辑器，Optimization Wizard 选择 RMS、Wavefront、Centroid、All Configurations，使用 Gaussian Quadrature。Ctrl+Shift+O 运行局部优化。只动空气隙，保持 THIC 6 的目标距离固定。</p>
<p>优化之后按上面的长度关系重新填写 THIC 1。不要把 3 mm 的负镜中心厚度设成变量，也不要用 Quick Focus 移动目标面来替代本题的动镜调焦。此处的准直入射模型下，补回前方空气段不改变入射波前；以后用真实束腰模型时须让两者联动。</p>
<h3>试一下高斯光束</h3><p>打开理想模型并切到配置 5，按 <kbd>Ctrl+B</kbd> 打开 Paraxial Gaussian Beam。波长选 1，Surf 1 to Waist=0。M²=1 时 Waist Size 填 <b>2 mm</b>；M²=5 且保持物理入射直径 4 mm 时，嵌入腰斑半径应填 <b>0.894427 mm</b>，不能仍填 2 mm。在 Image 面读 Size，注意这是半径，需要乘 2 得直径。M²=1 时对应 1/e² 高斯宽度；一般 M² 模型只是等效传播，不能推断任意实际光束的强度轮廓。</p>
<p>操作依据：<a href="https://ansyshelp.ansys.com/public/Views/Secured/Zemax/v252/en/OpticStudio_User_Guide/OpticStudio_Help/topics/Summary_of_Default_Shortcut_Keys.html">官方快捷键</a>、<a href="https://ansyshelp.ansys.com/public/Views/Secured/Zemax/v251/en/OpticStudio_User_Guide/OpticStudio_Help/topics/Changing_Configurations.html">切换配置</a>、<a href="https://ansyshelp.ansys.com/public/Views/Secured/Zemax/v251/en/OpticStudio_User_Guide/OpticStudio_Help/topics/Optimization_with_Multi_Configurations.html">多配置优化</a>。</p>'''

audit = '<h2>5. 对 Claude 原方案的审查</h2><ul><li>薄透镜公式与原第 1 步建模逻辑正确，原脚本已在独立 Zemax 实例实测；原文件未修改。</li><li>原脚本只做长焦理想模型，并不包含真实镜片、短焦方案或真实激光光斑验证。几何 RMS≈0 只证明理想成像成立。</li><li>本轮补齐了正镜固定的坐标关系、四种真实镜组、四种朝向比较、真实空气隙优化、有效孔径和重开检查。</li><li>口径按厂家保守保证值 90% 外径设置圆孔，不把机械外径当通光孔径。长焦理想模型 1 m 时的物镜处束径约 23.53 mm，已超过 Ø25.4 mm 镜片的 90% 保证口径 22.86 mm；本轮长焦平凸选 Ø30 mm，双胶合选 Ø50.8 mm。几何光线未截，不代表实际高斯尾部能量全部通过。</li><li>实际短焦候选并非精确 5 倍；当前占位镜座尺寸也未自动转换为真实镜片安装尺寸。</li><li>没有量化非球面的收益：本轮没有生成或声称已有非球面定型处方。实际已计算的收益来自双胶合与平凸的比较。</li></ul>'
zrows = []
for s in spots:
    if s['name'].startswith(('03','04','05','06')):
        zrows.append([s['name'][3:], f'{s["L_m"]:g}', f'{s["zernike_waves"].get("4",float("nan")):.6f}',
                      f'{s["zernike_waves"].get("11",float("nan")):.6f}',f'{s["zernike_waves"].get("22",float("nan")):.6f}'])
audit += '<details><summary>展开球差证据（Zemax Zernike Standard）</summary>'+table(['方案','距离 / m','Z4 离焦 / 波','Z11 初级球差 / 波','Z22 高阶球差 / 波'],zrows)+'<p>原始分析文字在“原始数据”文件夹。系数与 RMS 波前均使用各自分析的采样方式，微小差异正常；不要把单个系数直接当总 RMS。</p></details>'
audit += '<p>镜片来源：本机 OpticStudio 的 THORLABS 厂家目录，原始处方留在审查目录；型号与玻璃处方另对照 <a href="https://www.thorlabs.de/newgrouppage9.cfm?objectgroup_id=6510&pn=LC1054-B">Thorlabs 平凹镜</a>、<a href="https://www.thorlabs.us/newgrouppage9.cfm?objectgroup_id=112&pn=LA1002">平凸镜及口径规格</a>、<a href="https://www.thorlabs.de/newgrouppage9.cfm?objectgroup_id=259&pn=AC127-050-B">650–1050 nm 双胶合镜</a>。未核实即时库存或按功率完成选型。</p>'
audit += '<p>原脚本的 <code>S.New(False)</code> 会重置所连接的当前系统。本次在独立实例运行；以后若用 Interactive Extension 直接复跑原脚本，应先保存界面中已有的设计。</p>'
audit += '<h3>交付核验</h3><p>6 个主模型 × 2 种格式 × 5 个配置，60 次文件参数回读通过；12 组端点点列图，每组 1257 条光线，共 15084 条光线无错误、无截光；另有 60 个高斯条件案例与 38 个双胶合范围检查点。点列图的配置号与原生文字输出已逐一核对。模型参数保留较多小数是为了复算，不代表加工精度。</p><p>原始数值、厂家处方、运行脚本与 MCP 记录保存在包内。图中原生光路与数据重绘已区分。既有 SolidWorks 文件没有在本轮修改。</p>'

css = '''body{margin:0;background:#f2f5f7;color:#233442;font:16px/1.8 "Microsoft YaHei",sans-serif}main{max-width:1120px;margin:auto;padding:48px 44px 80px;background:white}h1{font-size:40px;line-height:1.35;letter-spacing:-1px}h2{margin-top:56px;padding-top:18px;border-top:1px solid #d8e3e8;font-size:25px}h3{margin-top:30px}.eyebrow{font-size:12px;letter-spacing:1px;color:#447a85}.lead{font-size:20px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:28px 0}.cards div{padding:22px;background:#edf5f4;border-radius:10px}.cards b{display:block;color:#137465;font-size:25px}.cards span{font-size:13px;color:#526670}.links{display:flex;gap:12px;flex-wrap:wrap}.links a{padding:8px 16px;border:1px solid #9dbbbd;border-radius:6px;text-decoration:none}a{color:#126b81}.note{padding:16px 20px;border-left:4px solid #c28a3c;background:#fff8eb}table{width:100%;border-collapse:collapse;font-size:14px;font-variant-numeric:tabular-nums}th{text-align:left;background:#edf2f5;font-weight:600}th,td{padding:11px 12px;border-bottom:1px solid #dce4e8;white-space:nowrap}.scroll{overflow:auto}figure{margin:24px 0}img{width:100%;height:auto;border:1px solid #e4eaed;border-radius:6px}figcaption{font-size:13px;color:#62727d;margin-top:6px}.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}details{margin:18px 0;padding:18px;border:1px solid #dbe5e8;border-radius:8px}summary{cursor:pointer;font-weight:600}kbd,code{background:#edf2f5;border-radius:4px;padding:2px 6px;font-size:14px}li{margin:12px 0}.steps li{padding-left:8px}footer{margin-top:45px;font-size:12px;color:#687e88}@media(max-width:750px){main{padding:25px 18px}h1{font-size:30px}.cards,.two{grid-template-columns:1fr}.cards b{font-size:22px}}@media print{main{max-width:none;padding:0}details{break-inside:avoid}.links{display:none}}'''
document = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Zemax 首轮结果与操作复盘</title><style>'+css+'</style><main>'+intro+main+models_html+beam+how+audit+'<footer>本地可离线阅读。模型和原始结果共同构成本轮证据；HTML 图表不会自动更新 Zemax 文件。</footer></main></html>'
(OUT / '先看这个_结果与操作复盘.html').write_text(document, encoding='utf-8')

text = f'''Zemax 首轮评估结论（915 nm，1–10 m）

已通过本机 Zemax MCP 实际运行。完整图文复盘：先看这个_结果与操作复盘.html。
6 个主模型在“模型”文件夹，每个都有 .zos 和 .zmx，含 1/2/3/5/10 m 五个配置。

结论：理想薄透镜方案成立，但不能据此证明实际激光全程 ≤5 mm。
长焦理想行程 24.186324 mm；短焦理想行程 5.514330 mm。
短焦双胶合可作为下一轮结构研究基线，行程 {short_best['travel_mm']:.6f} mm，
最差 RMS 波前 {short_best['worst_wfe_waves']:.6f} 波，出现在 1 m，未满足原说明 0.07 波要求。
长焦双胶合行程 {long_best['travel_mm']:.6f} mm，最差 {long_best['worst_wfe_waves']:.6f} 波，五个设计点都小于 0.07 波。
它使用 Ø50.8 mm 物镜，且行程超过当前 v0.9 已核验的 11.6 mm。

短焦型号：Thorlabs LC2265-B + AC254-075-B。负镜凹面朝输入，正镜翻转厂家原处方方向。
915 nm 下焦距比 {short_ratio:.6f}，不是精确 5.000，不能把名义“5 倍”当作严格验证通过。
空气隙 d 从负镜后顶点量到正镜前顶点；工作距离 L 从正镜后顶点量到目标面。
短焦 d 约 53–59 mm，不能直接套用原 CAD 120 mm 的镜片中心占位。

4 mm 入射直径尚未确认，M² 未知。Zemax 的条件高斯分析显示：固定物理入射直径 4 mm，
在 10 m、理想无截光情况下，M²=5 对应约 2.9 mm，M²=10 对应约 5.8 mm。
还需确认光斑直径定义、束径、M² 和束腰/发散角；真实像差和截光须纳入最终评估。

如何打开查看：
1. Ctrl+O 打开 模型\\06_短焦_双胶合.zos。
2. F7 打开多重结构表，双击配置 1 或 5 的列头切换 1 m / 10 m。
3. Ctrl+L 看光路；Ctrl+Shift+S 看点列图，在设置中选 Current 并勾选 Show Airy Disk。
4. Ctrl+Shift+U 更新所有分析窗口。几何 RMS Radius 是半径，不是实际光斑直径。

审查：原脚本只实现长焦理想模型；原建模逻辑实测通过，原文件没有修改。
原脚本 S.New(False) 会重置所连接的当前系统；本轮用独立实例，未清空界面中的设计。
本轮补了真实镜组、短焦组、四种朝向、多配置优化、光束条件评估和文件重开验证。
没有修改 SolidWorks，没有定型非球面，没有验证功率承受或热效应。
六个主模型的 .zmx/.zos 各五配置共 60 次回读通过，端点 15084 条几何光线无错误/截光。
所有数字来源区分：真实追迹/波前由 Zemax；间距理论公式、行程差值与图表整理为计算派生。
几何圆瞳模型和无截光的等效高斯模型是分开的条件模型，不应混同为一次真实激光仿真。
'''
(OUT / '审查反馈与结论.txt').write_text(text, encoding='utf-8-sig')
print(json.dumps({'html': str(OUT / '先看这个_结果与操作复盘.html'), 'figures': len(list(FIG.glob('*.png')))}, ensure_ascii=False))
