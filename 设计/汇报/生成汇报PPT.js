// 给老师的 3 页汇报（简洁版：一页一张图 + 一两句话；讲稿在备注里）。运行：node 生成汇报PPT.js
// 数字来自 ../工具/915nm评估.json、../工具/Z轴传动计算.json、../工具/结构参数.json（脚本算出）
const pptxgen = require('pptxgenjs');
const path = require('path'), fs = require('fs');
const { applyTheme } = require('/root/.claude/skills/synced/e3b20a92-3af7-48c8-b2d0-739bdf1b90ac_2220d486-52ca-4dd8-a908-32b12cc51d82/pptx/scripts/apply_theme.js');
const rd = f => JSON.parse(fs.readFileSync(path.join(__dirname, '../工具', f), 'utf8'));
const E = rd('915nm评估.json'), ZC = rd('Z轴传动计算.json'), F2 = rd('结构参数.json').f2;
const back = L => F2 * F2 / (L * 1000);
const THEME = { name: 'Plain', headFontFace: 'Microsoft YaHei', bodyFontFace: 'Microsoft YaHei',
  colors: { dk1: '1F2430', lt1: 'FFFFFF', dk2: '4A5262', lt2: 'F3F5F8', accent1: 'D63B3E', accent2: '2B7BB9', accent3: '8C96A6',
            accent4: '17914F', accent5: 'C99A3C', accent6: 'E0701C', hlink: '2B7BB9', folHlink: '6D5BA8' } };
const K = { dk: '1F2430', body: '3A4150', mute: '7A8291', red: 'D63B3E', green: '17914F', gray: '9AA1AD' };
(async () => {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_WIDE';
  pres.title = 'Z 轴动态聚焦系统'; pres.author = '激光动态聚焦项目';
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.defineSlideMaster({ title: 'PLAIN', background: { color: 'FFFFFF' },
    objects: [{ placeholder: { options: { name: 'title', type: 'title', x: 0.8, y: 0.5, w: 11.7, h: 0.75, fontSize: 28, bold: true, color: K.dk, margin: 0, valign: 'middle', align: 'left' }, text: '' } }],
    slideNumber: { x: 12.3, y: 7.0, w: 0.4, h: 0.3, fontSize: 10, color: K.gray, align: 'right' } });
  const para = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 16, color: K.body, breakLine: true, paraSpaceAfter: 12 }, o) });

  // 第 1 页：原理
  let s = pres.addSlide({ masterName: 'PLAIN' });
  s.addText('动态聚焦原理', { placeholder: 'title' });
  s.addImage({ path: path.join(__dirname, '素材/动图1_光路调焦.gif'), x: 1.15, y: 1.45, w: 11.0, h: 4.31, altText: '动图：动镜后退，焦点从 10 m 移到 1 m' });
  s.addText([para(`动镜与物镜组成 5 倍扩束镜（4 mm → ${E.D_mm} mm）。动镜后退，焦点由远处移到近处。`, { paraSpaceAfter: 0 })],
    { x: 1.15, y: 6.0, w: 11.0, h: 0.8, margin: 0, valign: 'top', isTextBox: true });
  s.addNotes(`光纤出来经准直头变成 4 mm 平行光；动镜（负透镜）把光撒开，物镜（正透镜）收拢成 ${E.D_mm} mm 的光束，两片合起来是 5 倍扩束镜。动镜往后退一点，出射光从平行变成微微汇聚，焦点就从远处移到近处：10 m 时动镜后退约 ${back(10).toFixed(1)} mm，1 m 时约 ${back(1).toFixed(1)} mm。扩束让光束变粗，远处光斑才小。后面接 XY 振镜扫描，控制卡同时控振镜（XY2-100）和 Z 轴电机（STEP/DIR）。换 915 nm 时机械和控制不用改，只换镀膜、重新标定。`);

  // 第 2 页：结构
  s = pres.addSlide({ masterName: 'PLAIN' });
  s.addText('调焦模块结构', { placeholder: 'title' });
  s.addImage({ path: path.join(__dirname, '素材/动图2_调焦模块传动.gif'), x: 0.5, y: 1.5, w: 8.7, h: 4.64, altText: '动图：电机带丝杆转，动镜在导轨上移动' });
  s.addText([
    para(`步进电机经联轴器带动丝杆（导程 1 mm），镜座沿导轨移动，每步 ${ZC.step_um.toFixed(2)} μm。`),
    para('丝杆断电自锁，消隙螺母消除回差。'),
    para(`1–10 m 需要约 ${E.travel.need} mm 行程；目前结构最近对焦约 ${E.travel.Lmin} m，下一版加长导轨。`, { color: K.mute, paraSpaceAfter: 0 })],
    { x: 9.45, y: 2.3, w: 3.4, h: 3.6, margin: 0, valign: 'top', isTextBox: true });
  s.addNotes(`电机通过波纹管联轴器带丝杆转，丝杆导程 1 mm：转一圈镜片走 1 mm，16 细分后一步约 ${ZC.step_um.toFixed(2)} μm。螺纹螺旋角 ${ZC.lam.toFixed(1)}° 小于摩擦角 ${ZC.phi.toFixed(1)}°，断电后推不动（自锁）；消隙螺母用弹簧把两半螺母顶开，换向不空走；钢球浮动接头只传推力。设计校核 16 项通过，电机力矩安全系数约 ${ZC.SF.toFixed(0)}，静态与运动干涉 0。要覆盖 1–10 m，动镜行程约 ${E.travel.need} mm，现结构最近对焦约 ${E.travel.Lmin} m；下一版加长导轨（或物镜换短焦，需 Zemax 核对像差）。`);

  // 第 3 页：激光器选型
  s = pres.addSlide({ masterName: 'PLAIN' });
  s.addText('激光器选型：M² 决定光斑大小', { placeholder: 'title' });
  const [sm, rq, cm] = E.curve.series;
  const req5 = E.req.find(r => r.L === 10 && r.d === 5);
  s.addChart(pres.charts.LINE, [
      { name: `M² ${sm.m2}（单模）`, labels: E.curve.dist.map(d => d + ' m'), values: sm.d },
      { name: `M² ${rq.m2}`, labels: E.curve.dist.map(d => d + ' m'), values: rq.d },
      { name: `M² ${cm.m2}（常见 915 nm）`, labels: E.curve.dist.map(d => d + ' m'), values: cm.d }], {
    x: 0.6, y: 1.45, w: 7.7, h: 5.3, chartColors: [K.green, K.red, K.gray], lineSize: 2.5, lineDataSymbol: 'none',
    showLegend: true, legendPos: 't', legendFontSize: 12, legendFontFace: '+mn-lt', legendColor: K.body,
    catAxisLabelColor: K.mute, valAxisLabelColor: K.mute, catAxisLabelFontSize: 12, valAxisLabelFontSize: 12, catAxisLabelFontFace: '+mn-lt', valAxisLabelFontFace: '+mn-lt',
    valGridLine: { color: 'EEF0F3', size: 0.75 }, catGridLine: { style: 'none' }, catAxisLineColor: 'C9CED6', valAxisLineShow: false,
    showValAxisTitle: true, valAxisTitle: '光斑直径（mm）', valAxisTitleFontSize: 12, valAxisTitleColor: K.mute, valAxisTitleFontFace: '+mn-lt',
    showCatAxisTitle: true, catAxisTitle: '工作距离（915 nm，出光 20 mm）', catAxisTitleFontSize: 12, catAxisTitleColor: K.mute, catAxisTitleFontFace: '+mn-lt' });
  s.addText([
    { text: '10 m 处光斑 ≤ 5 mm', options: { fontSize: 20, bold: true, color: K.dk, breakLine: true } },
    { text: `需要 M² ≤ ${req5.m2}`, options: { fontSize: 20, bold: true, color: K.red, breakLine: true, paraSpaceAfter: 18 } },
    para(`常见的 915 nm 激光器 M²≈${Math.round(cm.m2)}，10 m 处光斑约 ${cm.d.slice(-1)[0].toFixed(0)} mm。`),
    para(`选型时请厂家提供 M² 或 BPP 数据。`),
    para('d ≈ 4·M²·λ·L ÷ (π·D)', { fontSize: 14, color: K.mute, paraSpaceAfter: 0 })],
    { x: 8.8, y: 1.9, w: 4.0, h: 4.2, margin: 0, valign: 'top', isTextBox: true });
  const r1 = E.req.find(r => r.L === 1 && r.d === 1), r2 = E.req.find(r => r.L === 10 && r.d === 2);
  s.addNotes(`M² 是光束质量因子（有人叫模数）：理想单模 M² = 1，越大光越“乱”，聚出来的光斑越大。光斑直径 ≈ 4·M²·λ·L ÷ (π·D)，915 nm、出光 20 mm 时光斑与 M² 和距离成正比。图中三条线：单模 M² ${sm.m2}；要求线 M² ${rq.m2}（10 m 处正好 5 mm）；常见 915 nm 光纤耦合半导体（105 μm 芯径、NA 0.22）M² ≈ ${Math.round(cm.m2)}，1 m 约 ${cm.d[0].toFixed(1)} mm、10 m 约 ${cm.d.slice(-1)[0].toFixed(0)} mm。其他要求：10 m 处 ≤ 2 mm 需 M² ≤ ${r2.m2}；1 m 处 ≤ 1 mm 需 M² ≤ ${r1.m2}。若 M² 降不下来，可把出光口径加大到 30 mm（光斑 × 0.67，振镜要加大）。远场近似，未计像差与大气扰动。`);

  const out = path.join(__dirname, '动态聚焦系统汇报_v1.pptx');
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log('写出', out);
})();
