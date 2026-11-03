"""
需求：工作距离 5–50 m，光斑（1/e² 直径）≤ 5 mm。
算：① 激光器 M² 上限、出口光束要多粗；② 一个焦距设置能覆盖多远 → 需要几档；③ 连续调焦时 Z 要多准、行程多少。
高斯光束、薄透镜，不含像差和大气扰动。运行：python3 需求落地计算.py → 需求落地计算结果.md
"""
import math, os, datetime
LAM = 1.064e-3
L_NEAR, L_FAR = 5_000.0, 50_000.0     # mm【用户给定】
SPOT_MAX = 5.0                        # mm【用户给定】
M2 = 1.3                              # 【假设】
D_OUT = 20.0                          # mm，出口光束（方案 A：30 mm 振镜）
F2_LIST = [150.0, 300.0]              # mm，物镜焦距候选

def spot_at(L, F, D, m2):
    """出口光束直径 D，调成在 F 处成腰（F 太远则取最远可达），返回 L 处的光斑直径"""
    lp = m2 * LAM; W = D / 2; zr = math.pi * W * W / lp
    F = min(F, zr / 2 * 0.999999)
    a = F / zr**2; R = (1 - math.sqrt(1 - 4*a*F)) / (2*a)          # 会聚曲率半径
    q = 1 / complex(-1/R, -lp / (math.pi * W * W)) + L
    return 2 * math.sqrt(-lp / (math.pi * (1/q).imag))

def best_spot(L, D, m2):
    return min(spot_at(L, F, D, m2) for F in [L * (0.5 + k/400) for k in range(0, 401)])

out = [f"# 需求落地计算\n\n> 由 `工具/需求落地计算.py` 生成（{datetime.date.today()}）。需求：**5–50 m，光斑 ≤ 5 mm**（用户给定）。高斯光束、薄透镜，**不含像差和大气扰动**，真实光斑会更大，要留余量。\n"]

# ① M² 上限与光束粗细
out.append("## ① 激光器 M² 上限（50 m 处光斑 ≤ 5 mm）\n")
out.append("| 出口光束 | 对应振镜口径（×1.5） | M² 上限 | M² = 1.3 时 50 m 光斑 |\n|---|---|---|---|")
for D in [15, 20, 25, 33]:
    lo, hi = 1.0, 10.0
    if best_spot(L_FAR, D, 1.0) > SPOT_MAX: out.append(f"| {D} mm | {D*1.5:.0f} mm | 不可能 | — |"); continue
    for _ in range(40):
        mid = (lo + hi) / 2
        if best_spot(L_FAR, D, mid) <= SPOT_MAX: lo = mid
        else: hi = mid
    out.append(f"| {D} mm | {D*1.5:.0f} mm | **{lo:.2f}** | {best_spot(L_FAR, D, 1.3):.1f} mm |")

# ② 一个焦距能覆盖多远
def coverage(F, D=D_OUT, m2=M2):
    Ls = [L_NEAR + k * 50 for k in range(int((L_FAR - L_NEAR) / 50) + 1)]
    ok = [L for L in Ls if spot_at(L, F, D, m2) <= SPOT_MAX]
    return (min(ok), max(ok)) if ok else None
out.append(f"\n## ② 一个焦距设置能覆盖多远（出口 {D_OUT:.0f} mm，M² {M2}）\n")
out.append("| 焦点设在 | 光斑 ≤ 5 mm 的距离范围 |\n|---|---|")
for F in [5_000, 8_000, 12_000, 20_000, 30_000, 50_000]:
    c = coverage(F); out.append(f"| {F/1000:.0f} m | {c[0]/1000:.1f} – {c[1]/1000:.1f} m |" if c else f"| {F/1000:.0f} m | 无 |")
# 贪心：从远端开始，最少几档覆盖 5–50 m
presets = []; need = L_FAR
while need > L_NEAR - 1:
    best = None
    for F in [1000 * x / 10 for x in range(30, 1000)]:
        c = coverage(F)
        if c and c[1] >= need and (best is None or c[0] < best[1][0]): best = (F, c)
    if best is None: break
    presets.append(best); need = best[1][0] - 50
    if len(presets) > 10: break
out.append(f"\n**最少 {len(presets)} 档焦距就能覆盖 5–50 m：**\n")
out.append("| 档位 | 焦点设在 | 覆盖 |\n|---|---|---|")
for i, (F, c) in enumerate(presets): out.append(f"| {i+1} | {F/1000:.1f} m | {c[0]/1000:.1f} – {c[1]/1000:.1f} m |")

# ③ 连续调焦：允许的焦点误差 → 镜片位置公差
out.append(f"\n## ③ 连续调焦时，Z 要多准？\n")
out.append("焦点对准目标时，光斑 ≤ 5 mm 允许焦点前后偏多少，再折算成动镜位置公差（δ ≈ f2²/L）：\n")
hdr = "| 目标距离 | 允许焦点偏差 | " + " | ".join(f"f2={int(f)} mm 镜片公差" for f in F2_LIST) + " |"
out.append(hdr); out.append("|---|---|" + "---|" * len(F2_LIST))
for L in [5_000, 10_000, 20_000, 35_000, 50_000]:
    # 找允许的 F 窗口
    Fs = [L * (0.3 + k / 500) for k in range(0, 1001)]
    okF = [F for F in Fs if spot_at(L, F, D_OUT, M2) <= SPOT_MAX]
    if not okF: out.append(f"| {L/1000:.0f} m | 无 |" + " |" * len(F2_LIST)); continue
    Fmin, Fmax = min(okF), max(okF)
    tol = []
    for f2 in F2_LIST:
        d1, d2 = f2 * f2 / Fmin, f2 * f2 / Fmax
        tol.append(f"±{(d1 - d2) / 2 * 1000:.0f} μm")
    out.append(f"| {L/1000:.0f} m | {Fmin/1000:.1f} – {min(Fmax, 999e3)/1000:.1f} m | " + " | ".join(tol) + " |")
out.append("\n**行程**（5 → 50 m）：" + "；".join(f"f2 = {int(f)} mm 时 {f*f*(1/L_NEAR - 1/L_FAR):.2f} mm" for f in F2_LIST))
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "需求落地计算结果.md")
open(path, "w").write("\n".join(out) + "\n"); print("\n".join(out))
