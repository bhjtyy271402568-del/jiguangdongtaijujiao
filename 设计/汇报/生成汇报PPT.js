// 生成给老师的 3 页汇报：node 生成汇报PPT.js
// 数据来自 ../工具/915nm评估.json 和 ../工具/Z轴传动计算.json（由脚本算出）
const pptxgen = require('pptxgenjs');
const path = require('path'), fs = require('fs');
const { applyTheme } = require('/root/.claude/skills/synced/e3b20a92-3af7-48c8-b2d0-739bdf1b90ac_2220d486-52ca-4dd8-a908-32b12cc51d82/pptx/scripts/apply_theme.js');
const E = JSON.parse(fs.readFileSync(path.join(__dirname, '../工具/915nm评估.json'), 'utf8'));
const ZC = JSON.parse(fs.readFileSync(path.join(__dirname, '../工具/Z轴传动计算.json'), 'utf8'));
const F2 = JSON.parse(fs.readFileSync(path.join(__dirname, '../工具/结构参数.json'), 'utf8')).f2;
const back = L => F2 * F2 / (L * 1000);
const THEME = { name: 'LaserFocus', headFontFace: 'Microsoft YaHei', bodyFontFace: 'Microsoft YaHei',
  colors: { dk1: '1F2430', lt1: 'FFFFFF', dk2: '4A5262', lt2: 'F3F5F8', accent1: 'E5383B', accent2: '2B7BB9', accent3: 'C99A3C',
            accent4: '17914F', accent5: '8C96A6', accent6: 'E0701C', hlink: '2B7BB9', folHlink: '6D5BA8' } };
const HEX = { red: 'E5383B', blue: '2B7BB9', brass: 'C99A3C', green: '17914F', steel: '8C96A6', orange: 'E0701C', dk: '1F2430', mute: '6B7383', card: 'FFFFFF', bg: 'F3F5F8', line: 'DDE2E8' };
(async () => {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_WIDE'; // 13.33 × 7.5
  pres.title = 'Z 轴动态聚焦系统汇报'; pres.author = '激光动态聚焦项目';
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;
  pres.defineSlideMaster({ title: 'CONTENT', background: { color: HEX.bg },
    objects: [
      { text: { text: 'Z 轴动态聚焦系统 · 汇报', options: { x: 0.6, y: 7.0, w: 6, h: 0.3, fontSize: 10, color: HEX.mute, isTextBox: true, margin: 0 } } },
    ],
    slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: HEX.mute, align: 'right' },
    placeholders: undefined });
  pres.defineSlideMaster({ title: 'CONTENT_T', background: { color: HEX.bg },
    objects: [
      { placeholder: { options: { name: 'kicker', type: 'body', x: 0.6, y: 0.32, w: 12, h: 0.32, fontSize: 12, bold: true, color: HEX.red, margin: 0 }, text: '' } },
      { placeholder: { options: { name: 'title', type: 'title', x: 0.6, y: 0.62, w: 12.1, h: 0.75, fontSize: 30, bold: true, color: HEX.dk, margin: 0, valign: 'middle', align: 'left' }, text: '' } },
      { text: { text: 'Z 轴动态聚焦系统 · 汇报', options: { x: 0.6, y: 7.0, w: 6, h: 0.3, fontSize: 10, color: HEX.mute, isTextBox: true, margin: 0 } } },
    ],
    slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: HEX.mute, align: 'right' } });
  const shadow = () => ({ type: 'outer', color: '1F2430', blur: 8, offset: 2, angle: 90, opacity: 0.12 });
  const card = (s, x, y, w, h, name, fill = HEX.card) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: HEX.line, width: 0.75 }, shadow: shadow(), objectName: name });
  const num = (s, x, y, n, col = HEX.red) => { s.addShape(pres.shapes.OVAL, { x, y, w: 0.42, h: 0.42, fill: { color: col }, line: { color: col }, objectName: 'num' + n });
    s.addText(String(n), { x, y, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0, isTextBox: true }); };
  const stat = (s, x, y, w, big, small, col) => { card(s, x, y, w, 0.95, 'stat-' + small);
    s.addText([{ text: big, options: { fontSize: 24, bold: true, color: col, breakLine: true } }, { text: small, options: { fontSize: 11, color: HEX.mute } }],
      { x: x + 0.2, y: y + 0.08, w: w - 0.4, h: 0.8, margin: 0, valign: 'middle', isTextBox: true }); };

  // ========== 第 1 页：原理 ==========
  pres.addSection({ title: '原理' });
  let s = pres.addSlide({ masterName: 'CONTENT_T', sectionTitle: '原理' });
  s.addText('01  系统原理', { placeholder: 'kicker' });
  s.addText('动态聚焦怎么实现：一组“能动的扩束镜”', { placeholder: 'title' });
  card(s, 0.6, 1.55, 7.75, 4.25, 'gif1-card');
  s.addImage({ path: path.join(__dirname, '素材/动图1_光路调焦.gif'), x: 0.75, y: 1.95, w: 7.45, h: 2.92, altText: '动图：动镜后退，焦点从 10 m 移到 1 m' });
  s.addText(`动镜后退 → 焦点变近：对焦 10 m 时后退 ${back(10).toFixed(1)} mm，1 m 时后退 ${back(1).toFixed(1)} mm`, { x: 0.85, y: 5.25, w: 7.3, h: 0.4, fontSize: 13, color: HEX.dk2 || HEX.mute, margin: 0, isTextBox: true });
  const rows1 = [['准直头', '光纤出来的光变成 4 mm 粗的平行光'], ['动镜 + 物镜', '5 倍扩束到 20 mm；动镜前后移动，兼做调焦'], ['XY 振镜', '把光束扫到目标上的任意位置'], ['控制卡', 'XY2-100 控振镜，STEP / DIR 控 Z 电机，三轴同步']];
  rows1.forEach(([h, t], i) => { const y = 1.6 + i * 1.05; num(s, 8.7, y + 0.04, i + 1, i === 1 ? HEX.red : HEX.dk);
    s.addText([{ text: h, options: { fontSize: 16, bold: true, color: HEX.dk, breakLine: true } }, { text: t, options: { fontSize: 13, color: HEX.mute } }],
      { x: 9.3, y, w: 3.45, h: 0.95, margin: 0, valign: 'top', isTextBox: true }); });
  stat(s, 0.6, 6.0, 2.45, '5×', '扩束倍率（f 150 ÷ 30）', HEX.red);
  stat(s, 3.25, 6.0, 2.45, `${E.D_mm} mm`, '出光口径（配 30 mm 振镜）', HEX.blue);
  stat(s, 5.9, 6.0, 2.45, '1–10 m', '老师的工作距离', HEX.brass);
  card(s, 8.7, 6.0, 4.05, 0.95, 'note915', 'FDECEC');
  s.addText([{ text: '915 nm：', options: { bold: true, color: HEX.red } }, { text: '机械和控制通用，光学只需换 915 nm 镀膜并重新标定', options: { color: HEX.dk } }],
    { x: 8.9, y: 6.05, w: 3.7, h: 0.85, fontSize: 12, margin: 0, valign: 'middle', isTextBox: true });
  s.addNotes(`这页讲原理。光纤出来经准直头变成 4 mm 平行光；动镜（负透镜）把光撒开，物镜（正透镜）收拢成 20 mm 粗的光束，两片合起来是 5 倍扩束镜。动镜前后挪一点，出来的光就从平行变成微微汇聚，焦点就在 1–10 m 之间移动：10 m 时动镜后退约 ${back(10).toFixed(1)} mm，1 m 时约 ${back(1).toFixed(1)} mm。扩束让光束变粗，远处光斑才小。XY 振镜负责扫描，控制卡同时控制 XY 振镜和 Z 轴电机。换成 915 nm 时，机械和控制都不用改，只需换镀膜并重新标定 Z 位置表。`);

  // ========== 第 2 页：结构 ==========
  pres.addSection({ title: '结构' });
  s = pres.addSlide({ masterName: 'CONTENT_T', sectionTitle: '结构' });
  s.addText('02  调焦模块结构（v0.9）', { placeholder: 'kicker' });
  s.addText('丝杆推动镜片：细、断电自锁、没有回差', { placeholder: 'title' });
  card(s, 0.6, 1.55, 7.75, 4.4, 'gif2-card');
  s.addImage({ path: path.join(__dirname, '素材/动图2_调焦模块传动.gif'), x: 0.72, y: 1.66, w: 7.5, h: 4.0, altText: '动图：电机带丝杆转，动镜在导轨上前后移动' });
  const chain = [['步进电机', 'NEMA 11，16 细分'], ['波纹管联轴器', '吸收不同心，转动无间隙'], ['丝杆 Ø5 · 导程 1 mm', `螺旋角 ${ZC.lam.toFixed(1)}° < 摩擦角 ${ZC.phi.toFixed(1)}° → 断电自锁`], ['消隙螺母', '弹簧把两半螺母顶开 → 无回差'], ['钢球浮动接头', '只传推力，丝杆摆动不传给镜片'], ['导轨滑块 + 墓碑形镜座', '动镜沿光轴平移']];
  chain.forEach(([h, t], i) => { const y = 1.55 + i * 0.735; num(s, 8.7, y + 0.06, i + 1, i === 2 ? HEX.red : HEX.dk);
    s.addText([{ text: h, options: { fontSize: 14, bold: true, color: HEX.dk, breakLine: true } }, { text: t, options: { fontSize: 11.5, color: HEX.mute } }],
      { x: 9.3, y, w: 3.5, h: 0.68, margin: 0, valign: 'top', isTextBox: true }); });
  stat(s, 0.6, 6.0, 2.45, `${ZC.step_um.toFixed(2)} μm`, '电机走一步，镜片移动', HEX.red);
  stat(s, 3.25, 6.0, 2.45, `× ${ZC.SF.toFixed(0)}`, '电机力矩安全系数', HEX.blue);
  stat(s, 5.9, 6.0, 2.45, '0 处', '干涉（含行程两端运动）', HEX.green);
  card(s, 8.7, 6.0, 4.05, 0.95, 'travel', 'FFF4E5');
  s.addText([{ text: '1–10 m 需行程约 ' + E.travel.need + ' mm：', options: { bold: true, color: HEX.orange } }, { text: `现结构最近对焦约 ${E.travel.Lmin} m，下一版加长导轨或物镜换短焦`, options: { color: HEX.dk } }],
    { x: 8.9, y: 6.05, w: 3.7, h: 0.85, fontSize: 12, margin: 0, valign: 'middle', isTextBox: true });
  s.addNotes(`这页讲调焦模块。电机通过波纹管联轴器带丝杆转，丝杆导程 1 mm，转一圈镜片走 1 mm；16 细分后一步约 ${ZC.step_um.toFixed(2)} μm。螺纹很平（螺旋角 ${ZC.lam.toFixed(1)}°，小于摩擦角 ${ZC.phi.toFixed(1)}°），断电后推不动，能自锁。消隙螺母用弹簧把两个半螺母顶开，换方向不空走。钢球浮动接头只传推力。设计校核 16 项全过，电机力矩安全系数约 ${ZC.SF.toFixed(0)}，静态和运动干涉都是 0。老师要 1–10 m：动镜行程需约 ${E.travel.need} mm，现在结构最近能对焦到约 ${E.travel.Lmin} m；下一版两种改法：加长导轨行程，或者物镜换短焦（行程变短但像差要用 Zemax 核对）。`);

  // ========== 第 3 页：激光器怎么选 ==========
  pres.addSection({ title: '选型' });
  s = pres.addSlide({ masterName: 'CONTENT_T', sectionTitle: '选型' });
  s.addText('03  激光器怎么选（915 nm，出光 20 mm）', { placeholder: 'kicker' });
  s.addText('光斑大小主要看激光器的 M²：M² 越小，光斑越小', { placeholder: 'title' });
  card(s, 0.6, 1.55, 6.9, 5.35, 'chart-card');
  const cols = [HEX.green, HEX.blue, HEX.brass, HEX.orange, HEX.red];
  s.addChart(pres.charts.LINE, E.curve.series.map(se => ({ name: `M² = ${se.m2}`, labels: E.curve.dist.map(d => d + ' m'), values: se.d })), {
    x: 0.75, y: 1.65, w: 6.6, h: 5.15, showTitle: true, title: '各距离的光斑直径（mm）', titleFontSize: 14, titleColor: HEX.dk, titleFontFace: '+mj-lt',
    chartColors: cols, lineSize: 2.5, lineDataSymbol: 'circle', lineDataSymbolSize: 6,
    showLegend: true, legendPos: 'b', legendFontSize: 11, legendFontFace: '+mn-lt', legendColor: HEX.dk,
    catAxisLabelColor: HEX.mute, valAxisLabelColor: HEX.mute, catAxisLabelFontSize: 11, valAxisLabelFontSize: 11, catAxisLabelFontFace: '+mn-lt', valAxisLabelFontFace: '+mn-lt',
    valGridLine: { color: 'E3E7EC', size: 0.75 }, catGridLine: { style: 'none' },
    showValAxisTitle: true, valAxisTitle: '光斑直径 (mm)', valAxisTitleFontSize: 11, valAxisTitleColor: HEX.mute, valAxisTitleFontFace: '+mn-lt',
    showCatAxisTitle: true, catAxisTitle: '工作距离', catAxisTitleFontSize: 11, catAxisTitleColor: HEX.mute, catAxisTitleFontFace: '+mn-lt' });
  card(s, 7.75, 1.55, 5.0, 1.45, 'formula');
  s.addText([{ text: '光斑直径  d ≈ 4 · M² · λ · L ÷ (π · D)', options: { fontSize: 16, bold: true, color: HEX.dk, breakLine: true } },
             { text: 'λ = 0.915 μm，L = 距离，D = 出光口径 20 mm', options: { fontSize: 11.5, color: HEX.mute, breakLine: true } },
             { text: '光纤激光器：M² ≈ (芯径 ÷ 2 × NA) ÷ (λ ÷ π)', options: { fontSize: 11.5, color: HEX.mute } }],
    { x: 7.95, y: 1.65, w: 4.65, h: 1.25, margin: 0, valign: 'middle', isTextBox: true });
  const pick = [[10, 2], [10, 5], [10, 10], [1, 0.5], [1, 1]];
  const req = pick.map(([L, d]) => E.req.find(r => r.L === L && r.d === d));
  const hdr = { bold: true, color: 'FFFFFF', fill: { color: HEX.dk }, fontSize: 12, align: 'center', valign: 'middle' };
  const cell = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 12, color: HEX.dk, align: 'center', valign: 'middle' }, o) });
  s.addTable([[{ text: '距离', options: hdr }, { text: '光斑要 ≤', options: hdr }, { text: 'M² 需 ≤', options: hdr }, { text: 'BPP ≤ (mm·mrad)', options: hdr }],
    ...req.map((r, i) => [cell(r.L + ' m'), cell(r.d + ' mm'), cell(String(r.m2), { bold: true, color: HEX.red }), cell(String(r.bpp))].map(c => (c.options.fill = { color: i % 2 ? 'F6F8FA' : 'FFFFFF' }, c)))],
    { x: 7.75, y: 3.2, w: 5.0, colW: [0.9, 1.15, 1.15, 1.8], rowH: 0.36, border: { type: 'solid', color: HEX.line, pt: 0.75 } });
  card(s, 7.75, 5.55, 5.0, 1.35, 'advice', 'EAF5EE');
  const common = E.sources.find(x => x.name.includes('最常见'));
  s.addText([{ text: '建议：', options: { bold: true, color: HEX.green } },
             { text: `常见 915 nm（105 μm / NA 0.22，M² ≈ ${Math.round(common.m2)}）在 10 m 处光斑约 ${E.curve.series.find(x => x.m2 === 40).d.slice(-1)[0].toFixed(0)} mm。若要 10 m 处 ≤ 5 mm，选 `, options: { color: HEX.dk } },
             { text: `M² ≤ ${req[1].m2}`, options: { bold: true, color: HEX.red } },
             { text: '（向厂家要 M² 或 BPP），或把出光加大到 30 mm（光斑 × 0.67）。', options: { color: HEX.dk } }],
    { x: 7.95, y: 5.62, w: 4.65, h: 1.2, fontSize: 12, margin: 0, valign: 'middle', isTextBox: true });
  s.addNotes(`这页讲激光器怎么选。M² 是光束质量因子（也有人叫模数）：理想单模光束 M² = 1，越大光越“乱”，聚出来的光斑越大。光斑直径 ≈ 4·M²·λ·L ÷ (π·D)，在 915 nm、出光 20 mm 时，光斑和 M²、距离成正比。图里五条线分别是 M² = 1.2 到 40。常见的 915 nm 光纤耦合半导体激光器（105 μm 芯径、NA 0.22）M² 约 40，10 m 处光斑约 23 mm，1 m 处约 2.3 mm。反过来，想要 10 m 处光斑 ≤ 5 mm，M² 要 ≤ ${req[1].m2}（BPP ≤ ${req[1].bpp} mm·mrad）；1 m 处 ≤ 1 mm，M² 要 ≤ ${req[4].m2}。所以选型时要向厂家要 M² 或 BPP 数据；如果 M² 降不下来，也可以把出光口径加大（30 mm 时光斑变为 0.67 倍，振镜口径要跟着加大）。计算是远场近似，没算像差和大气扰动，实际会略大。`);

  const out = path.join(__dirname, '动态聚焦系统汇报_v1.pptx');
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log('写出', out);
})();
