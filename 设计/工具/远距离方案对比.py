"""
远距离（几十米）前聚焦：方案对比（高斯光束，薄透镜，不含像差/大气扰动）
用法：改“参数”，运行 python3 远距离方案对比.py → 生成 远距离方案对比结果.md
"""
import math, os, datetime
LAM = 1.064e-3                 # mm
M2  = 1.3                      # 【假设】激光器未定型号
L_DESIGN = 50_000.0            # mm，设计工作距离【用户给定 50 m】
DISTS = [10_000, 20_000, 30_000, 50_000]   # mm，用来看趋势
LENS_ERR = 0.5e-3              # mm，动镜重复性【资料】SCANLAB < 0.5 μm（R030）
ANG_REP = 8e-6                 # rad，振镜角重复性【资料】R001
# 方案：最后一个光学元件处的光束 1/e² 直径 D、指向方式、所需反射镜口径（D×1.5）
ARCH = [
  ("A 振镜 30 mm 口径", 20.0, "振镜（XY2-100，可直接用控制卡）"),
  ("B 大振镜 50 mm 口径", 33.0, "大口径振镜（更慢、更贵）"),
  ("C 望远镜 100 mm 出口 + 云台", 70.0, "云台（类似艾思兰除障/除冰，R007/R008）"),
]
LP = M2 * LAM

def focus(W, L):
    """出口光束半径 W，调曲率让束腰落在 L 处：返回 束腰半径, 瑞利长度"""
    zr_out = math.pi * W * W / LP
    if L > zr_out / 2: return None, None           # 聚不到这么远
    # 解 R：束腰位置 z = R / (1 + (R/zr_out)^2) = L，取较小根（真正会聚）
    a = L / zr_out**2; disc = 1 - 4 * a * L
    R = (1 - math.sqrt(disc)) / (2 * a)
    w0 = W / math.sqrt(1 + (zr_out / R) ** 2)
    return w0, math.pi * w0 * w0 / LP

out = [f"# 远距离前聚焦：方案对比\n\n> 由 `工具/远距离方案对比.py` 生成（{datetime.date.today()}）。高斯光束、薄透镜，**不含像差和大气扰动**（几十米的真实光斑会更大）。M² = {M2}（【假设】，激光器未定）。\n"]
out.append("## 1. 三种方案在 50 m 处\n")
out.append("| 方案 | 出口光束 | 50 m 光斑 | 焦深 ± | 最远能聚焦到 | 指向精度（8 μrad） | 指向方式 |\n|---|---|---|---|---|---|---|")
for name, D, how in ARCH:
    w0, zr = focus(D / 2, L_DESIGN)
    zmax = math.pi * (D / 2) ** 2 / LP / 2
    out.append(f"| {name} | {D:.0f} mm | {2*w0:.1f} mm | {0.458*zr/1000:.1f} m | {zmax/1000:.0f} m | {ANG_REP*L_DESIGN:.1f} mm | {how} |")
out.append("\n## 2. 方案 A 随距离的变化\n")
out.append("| 距离 | 光斑 | 焦深 ± |\n|---|---|---|")
for L in DISTS:
    w0, zr = focus(10.0, L)
    out.append(f"| {L/1000:.0f} m | {2*w0:.2f} mm | {0.458*zr/1000:.2f} m |")
out.append("\n## 3. M² 的影响（方案 A，出口 20 mm，50 m 处能做到的最小光斑）\n")
out.append("| 激光器 M² | 50 m 最小光斑 | 说明 |\n|---|---|---|")
def min_spot(W, L, lp):
    best = 1e9
    for k in range(0, 4001):
        c = k / 4000 * 2 / L                       # 会聚曲率 1/R
        inv_q = complex(-c, -lp / (math.pi * W * W))
        q = 1 / inv_q + L
        w = math.sqrt(-lp / (math.pi * (1 / q).imag))
        best = min(best, w)
    return 2 * best
for m2, note in [(1.1, "单模光纤激光器"), (1.3, "本文假设"), (3, "少模"), (10, "高功率多模（示意）")]:
    out.append(f"| {m2} | {min_spot(10.0, L_DESIGN, m2*LAM):.1f} mm | {note} |")
out.append("\n## 4. 动镜行程（伽利略式调焦，δ ≈ f2² × (1/L近 − 1/L远)）\n")
out.append("| 物镜（定镜）焦距 f2 | 对焦 10→50 m 行程 | 对焦 40→60 m 行程 | 0.5 μm 误差 → 50 m 处焦点误差 |\n|---|---|---|---|")
for f2 in [60, 150, 300]:
    t1 = f2**2 * (1/10_000 - 1/50_000); t2 = f2**2 * (1/40_000 - 1/60_000)
    err = (L_DESIGN**2 / f2**2) * LENS_ERR
    out.append(f"| {f2} mm | {t1:.2f} mm | {t2:.3f} mm | {err/1000:.2f} m |")
th = math.radians(2)
out.append(f"\n## 5. 扫描时还要不要弧面补偿？\n\n50 m 处振镜扫 ±2°（宽约 {2*L_DESIGN*math.tan(th)/1000:.1f} m），边上弧面只差 **{(L_DESIGN/math.cos(th)-L_DESIGN):.0f} mm**，远小于焦深（方案 A 约 ±{0.458*focus(10.0, L_DESIGN)[1]/1000:.1f} m）→ **扫描时 Z 基本不用动**。")
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "远距离方案对比结果.md")
open(path, "w").write("\n".join(out) + "\n"); print("\n".join(out))
