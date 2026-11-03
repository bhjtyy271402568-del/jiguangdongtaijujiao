"""
调焦头（5–50 m 前聚焦）结构参数：唯一数据源
- 输出 结构参数.json（给 3D 课件和 CadQuery 模型用）和 结构参数结果.md（布局表 + 公差计算）
- 坐标：光轴沿 +X，Y 向左，Z 向上；底板上表面 Z=0；单位 mm
- 【假设】的尺寸在选定具体型号后替换
"""
import json, math, os, datetime
F1, F2 = -30.0, 150.0            # 动镜 / 物镜焦距【推算】v0.5
S0 = F2 + F1                      # 平行光出射时的镜间距 = 120
L_NEAR, L_FAR = 5000.0, 50000.0
AXIS_H = 50.0                     # 光轴高度【假设】
TRAVEL = F2**2 * (1/L_NEAR - 1/L_FAR)   # 4.05 mm【推算】

X_OBJ = 290.0                     # 物镜中心
X_L1_INF = X_OBJ - S0             # 动镜在“对焦无穷远”时的位置
parts = [
 # name, kind, x(中心), 尺寸, 说明, 来源
 dict(id="base",  name="底板",           kind="box", x=245, y=0, z=-6, L=520, W=170, H=12, note="铝板 12 mm；所有安装座的基准面", src="【假设】"),
 dict(id="laser", name="激光准直器（输出头）", kind="cyl", x=45, y=0, z=AXIS_H, D=30, L=80, note="光纤激光器输出头；型号未定，用可换的夹持座 + 两轴俯仰调节", src="【假设】"),
 dict(id="comb",  name="合束镜（45°）",   kind="mirror", x=120, y=0, z=AXIS_H, D=25.4, note="1064 透、红光反；运动学镜座（两轴调）", src="【假设】"),
 dict(id="red",   name="红光指示模组",    kind="cyl_y", x=120, y=55, z=AXIS_H, D=12, L=40, note="从侧面打到合束镜，和主光同轴", src="【假设】"),
 dict(id="stage", name="丝杠滑台",        kind="box", x=X_L1_INF - 2, y=0, z=AXIS_H/2 - 6, L=60, W=40, H=AXIS_H - 22, note=f"交叉滚柱导轨 + 1 mm 导程丝杠；行程 ≥ 10 mm（需要 {TRAVEL:.2f} mm）", src="【推算】/【假设】"),
 dict(id="motor", name="步进电机（28 mm）", kind="box", x=X_L1_INF - 50, y=0, z=AXIS_H/2 - 6, L=34, W=28, H=28, note="NEMA 11；16 细分约 0.31 μm/步；后端装原点开关", src="【假设】"),
 dict(id="l1",    name="动镜 f1 = −30 mm", kind="lens", x=X_L1_INF, y=0, z=AXIS_H, D=12.7, note="Ø12.7 负透镜，装在滑台上；越轻越好", src="【推算】"),
 dict(id="obj",   name="物镜 f2 = 150 mm", kind="lens", x=X_OBJ, y=0, z=AXIS_H, D=40, note="Ø40 双胶合（通光 ≥ 28 mm）；镜座带 XY 对中调节", src="【推算】/【假设】"),
 dict(id="tube",  name="遮光筒",           kind="tube", x=(X_L1_INF + X_OBJ)/2 + 5, y=0, z=AXIS_H, D=48, L=S0 - 20, note="挡杂散光、防尘；不受力", src="【假设】"),
 dict(id="galvo", name="XY 振镜头（30 mm 口径）", kind="box", x=X_OBJ + 105, y=0, z=AXIS_H, L=130, W=110, H=88, note="入口在后面，出口在前面（示意）；型号未定，用转接板对准光轴", src="【假设】"),
 dict(id="window", name="保护窗",          kind="lens", x=X_OBJ + 178, y=0, z=AXIS_H, D=80, note="1064 双面增透平板，快拆；尺寸取决于扫描角", src="【假设】"),
 dict(id="shell", name="外壳",             kind="shell", x=245, y=0, z=58, L=520, W=170, H=140, note="防尘、遮光；前面开窗", src="【假设】"),
]
# —— 公差计算 ——
def point_shift_mm(decenter_um, L_mm): return decenter_um*1e-3 / F2 * L_mm      # θ = e / f2
tol = dict(
  travel=TRAVEL,
  decenter_rows=[(e, point_shift_mm(e, 50000), point_shift_mm(e, 5000)) for e in [1, 2, 5, 10]],
  thermal_um=23e-6 * S0 * 10 * 1000,            # 铝，ΔT=10 K
)
data = dict(generated=str(datetime.date.today()), axis_h=AXIS_H, f1=F1, f2=F2, s0=S0, travel=TRAVEL, x_l1_inf=X_L1_INF, x_obj=X_OBJ, parts=parts)
here = os.path.dirname(os.path.abspath(__file__))
json.dump(data, open(os.path.join(here, "结构参数.json"), "w"), ensure_ascii=False, indent=1)

md = [f"# 调焦头结构参数（自动生成，{data['generated']}）\n", "> 由 `工具/结构参数.py` 生成。坐标：光轴沿 +X，Z 向上，底板上表面 Z = 0，单位 mm。\n",
      "## 布局\n", "| 部件 | 位置 X | 尺寸 | 说明 | 来源 |\n|---|---|---|---|---|"]
for p in parts:
    size = f"Ø{p['D']}" + (f" × {p['L']}" if 'L' in p and p['kind'] in ('cyl','cyl_y','tube') else "") if 'D' in p else f"{p['L']} × {p['W']} × {p['H']}"
    md.append(f"| {p['name']} | {p['x']:.0f} | {size} | {p['note']} | {p['src']} |")
md += [f"\n光轴高度 {AXIS_H} mm；动镜 → 物镜间距 {S0:.0f} mm（对焦无穷远），对焦 5 m 时再拉开 {TRAVEL:.2f} mm（动镜往激光器方向走）。\n",
       "## 公差 1：动镜横向晃动 → 远处光点偏移\n", "动镜横向偏 e，出射光偏转 θ ≈ e / f2（f2 = 150 mm）。\n",
       "| 动镜横向偏移 | 50 m 处光点偏 | 5 m 处光点偏 |\n|---|---|---|"]
for e, a, b in tol['decenter_rows']: md.append(f"| {e} μm | {a:.2f} mm | {b:.3f} mm |")
md += ["\n- **能重复的偏移**（每次走到同一位置都一样）：可以标定掉，由控制卡按 Z 位置给 XY 加偏移量",
       "- **不能重复的晃动**：标定不掉，要靠滑台本身。若允许 50 m 处随机偏移 ≤ 1 mm【假设】，滑台的不可重复横向晃动要 ≤ 3 μm",
       "- 物镜静态偏心同理（θ = e / f2），是固定偏差，装调对中或标定即可\n",
       "## 公差 2：热胀\n", f"铝遮光筒 / 底板在动镜—物镜之间 {S0:.0f} mm，温度变化 10 K 时伸长约 **{tol['thermal_um']:.0f} μm**，相当于 50 m 处焦点公差（±50 μm）的一半以上 → 需要温度补偿或标定。\n",
       "## 公差 3：丝杠回差\n", "普通丝杠回差可能有几十 μm → 用预紧螺母或滚珠丝杠，或者每次都从同一方向走到目标（单向趋近）。\n"]
open(os.path.join(here, "结构参数结果.md"), "w").write("\n".join(md) + "\n")
print("\n".join(md))
