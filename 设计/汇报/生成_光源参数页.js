// 单页汇报：光学设计能力已具备，具体设计需要光源参数。运行：node 生成_光源参数页.js
// 数字来源：设计/审查/Zemax结果_v0.2_审查.md（B 方案行程 7.9 mm）、设计/工具/准直镜核算结果.md（MFD → 焦距）
const pptxgen = require('pptxgenjs');
const path = require('path');
const SK = '/root/.claude/skills/synced/e3b20a92-3af7-48c8-b2d0-739bdf1b90ac_2220d486-52ca-4dd8-a908-32b12cc51d82/pptx/scripts/apply_theme.js';
const { applyTheme } = require(SK);
const THEME = { name: 'Plain', headFontFace: 'Microsoft YaHei', bodyFontFace: 'Microsoft YaHei',
  colors: { dk1: '1F2430', lt1: 'FFFFFF', dk2: '4A5262', lt2: 'F3F5F8', accent1: 'D63B3E', accent2: '2B7BB9', accent3: '8C96A6',
            accent4: '17914F', accent5: 'C99A3C', accent6: 'E0701C', hlink: '2B7BB9', folHlink: '6D5BA8' } };
const K = { dk: '1F2430', body: '3A4150', mute: '7A8291', red: 'D63B3E', green: '17914F', blue: '2B7BB9', line: 'D8DEE7', soft: 'F3F5F8' };
(async () => {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_WIDE';
  pres.title = '光学设计能力与光源参数'; pres.author = '激光动态聚焦项目';
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.defineSlideMaster({ title: 'PLAIN', background: { color: 'FFFFFF' },
    objects: [{ placeholder: { options: { name: 'title', type: 'title', x: 0.8, y: 0.45, w: 11.7, h: 0.75, fontSize: 28, bold: true, color: K.dk, margin: 0, valign: 'middle', align: 'left' }, text: '' } }],
    slideNumber: { x: 12.3, y: 7.0, w: 0.4, h: 0.3, fontSize: 10, color: '9AA1AD', align: 'right' } });
  const s = pres.addSlide({ masterName: 'PLAIN' });
  s.addText('光学设计进展及所需激光器参数', { placeholder: 'title' });

  // 左：已经能做
  const LX = 0.8, LW = 5.5;
  s.addText('已经能做', { x: LX, y: 1.45, w: LW, h: 0.45, fontSize: 18, bold: true, color: K.green, margin: 0, isTextBox: true });
  const CAN = [
    ['动态聚焦光路', 'Zemax 建模、选镜片、优化：1–10 m 动镜只走 7.9 mm，10 m 光斑 < 1 mm（要求 ≤ 5 mm）'],
    ['准直镜', '按光纤参数推出焦距，选镜片朝向，核算像差、装调公差和回光'],
    ['仿真验证', '物理光学传播（POP）看任意距离的真实光斑，滑块扫描 1–10 m']];
  CAN.forEach(([h, t], i) => {
    const y = 2.0 + i * 1.32;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: LX, y, w: LW, h: 1.12, rectRadius: 0.08, fill: { color: K.soft }, line: { color: K.soft }, objectName: `能力卡${i + 1}` });
    s.addShape(pres.shapes.OVAL, { x: LX + 0.22, y: y + 0.3, w: 0.5, h: 0.5, fill: { color: K.green }, line: { color: K.green }, objectName: `能力号${i + 1}` });
    s.addText(String(i + 1), { x: LX + 0.22, y: y + 0.3, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0, isTextBox: true });
    s.addText([{ text: h, options: { fontSize: 16, bold: true, color: K.dk, breakLine: true } }, { text: t, options: { fontSize: 13, color: K.body } }],
      { x: LX + 0.9, y: y + 0.1, w: LW - 1.05, h: 0.92, margin: 0, valign: 'middle', isTextBox: true });
  });

  // 右：需要光源提供
  const RX = 6.8, RW = 5.75;
  s.addText('需要光源提供（激光器规格书）', { x: RX, y: 1.45, w: RW, h: 0.45, fontSize: 18, bold: true, color: K.red, margin: 0, isTextBox: true });
  const hd = t => ({ text: t, options: { bold: true, color: 'FFFFFF', fill: { color: '4A5262' }, fontSize: 13 } });
  const ROWS = [
    ['波长', '镜片材料、镀膜、焦距'],
    ['输出方式：QBH 裸纤 / 自带准直（输出直径）', '要不要自己做准直镜、扩束倍率'],
    ['模场直径 MFD（或纤芯 + NA）', '准直镜焦距：14 μm → 约 40 mm，20 μm → 约 60 mm'],
    ['光束质量 M²', '远处光斑大小'],
    ['功率、连续 / 脉冲', '散热、镀膜耐受、回光防护'],
    ['接头型号（QBH / QD）、端帽', '机械接口、光纤到镜片的距离']];
  s.addTable([[hd('参数'), hd('决定什么')], ...ROWS.map(([a, b], i) => [
      { text: a, options: { bold: true, color: K.dk, fill: { color: i % 2 ? 'FFFFFF' : 'F7F8FA' } } },
      { text: b, options: { color: K.body, fill: { color: i % 2 ? 'FFFFFF' : 'F7F8FA' } } }])],
    { x: RX, y: 2.0, w: RW, colW: [2.65, 3.1], fontSize: 12.5, fontFace: 'Microsoft YaHei', border: { type: 'solid', pt: 0.75, color: K.line }, rowH: 0.52, valign: 'middle', margin: [0.04, 0.1, 0.04, 0.1] });

  // 底：拿到参数之后的流程
  const FLOW = ['拿到规格书', '定准直镜焦距', '准直 + 动态聚焦联合仿真', '出镜片清单和结构图'];
  const FY = 6.15, FW = 2.6, GAP = 0.43;
  FLOW.forEach((t, i) => {
    const x = 0.8 + i * (FW + GAP);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: FY, w: FW, h: 0.62, rectRadius: 0.1, fill: { color: i === 0 ? K.red : 'FFFFFF' }, line: { color: i === 0 ? K.red : K.blue, width: 1.25 }, objectName: `流程${i + 1}` });
    s.addText(t, { x, y: FY, w: FW, h: 0.62, fontSize: 14, bold: true, color: i === 0 ? 'FFFFFF' : K.blue, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
    if (i < FLOW.length - 1) s.addText('→', { x: x + FW, y: FY, w: GAP, h: 0.62, fontSize: 22, bold: true, color: K.blue, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
  });

  s.addNotes('光学设计这一块现在已经能独立做：动态聚焦光路用 Zemax 建模和优化，B 方案（熔石英负透镜 + 两片物镜）在 1–10 m 动镜只走 7.9 mm，10 m 处光斑不到 1 mm，比要求的 5 mm 小很多；准直镜可以按光纤参数推出焦距、选朝向，核算像差、装调公差和回光；用物理光学传播可以看任意距离的真实光斑。但具体镜片要定下来，必须先有激光器的规格书。最关键的是模场直径 MFD：它直接决定准直镜焦距，14 μm 对应约 40 mm，20 μm 对应约 60 mm。另外要知道输出是 QBH 裸纤还是自带准直、输出直径多少（决定要不要自己做准直、扩束倍率是否要改），M²（决定远处光斑），功率和工作方式（决定散热和镀膜），接头和端帽（决定机械接口）。拿到规格书后，按图下方的流程推进：定准直镜焦距 → 准直和动态聚焦联合仿真 → 出镜片清单和结构图。');

  const out = path.join(__dirname, '光学设计能力与光源参数.pptx');
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log('写出', out);
})();
