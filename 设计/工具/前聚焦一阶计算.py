"""
前聚焦动态聚焦：一阶光学计算（高斯光束 ABCD，薄透镜）
用法：改下面的“设计参数”，运行  python3 前聚焦一阶计算.py
输出：同目录下的 前聚焦一阶计算结果.md
说明：薄透镜 + 嵌入式高斯光束（用 M²·λ 代替 λ），不含像差、热效应和截光。只用来定方向、给 Zemax 起点。
"""
import math, cmath, os, datetime

# ===== 设计参数（【假设】标注的请按实际修改）=====
LAM      = 1.064e-3   # mm，波长
M2       = 1.3        # 光束质量【资料】验证清单示例；待激光器型号
D_LASER  = 4.0        # mm，激光器出光 1/e² 直径【假设】
EXP_FIX  = 2.0        # 固定扩束倍数【推算】
F1       = -24.0      # mm，动镜（负）焦距【假设】
F2       = 60.0       # mm，定镜（正）焦距【假设】
G        = 80.0       # mm，定镜 → 振镜（第二片）的光程【假设】
APERTURE = 30.0       # mm，振镜口径【资料】SCANLAB PR 典型 30 mm（R030）
L_MIN, L_MAX = 500.0, 2000.0   # mm，振镜 → 目标的工作距离范围【假设】
THETA    = math.atan(0.44)     # 单边扫描角（光学）【推算】由 AXIALSCAN 反推（R036）
LENS_ERR = 0.5e-3     # mm，动镜位置误差（重复性）【资料】SCANLAB < 0.5 μm（R030）
SPOT_V   = 2000.0     # mm/s，光点扫描速度（用于估算动镜速度需求）【假设】
LENS_VMAX= 140.0      # mm/s，动镜速度上限【资料】SCANLAB 40i（R030）
# ================================================

LP = M2 * LAM                       # 嵌入式高斯的等效波长
S0 = F2 + F1                        # 平行光出射时的镜间距（伽利略式）

def q_after(s):
    """动镜处为扩束后平行光的束腰；返回定镜之后的 q 参数"""
    w = D_LASER * EXP_FIX / 2
    q = 1j * math.pi * w * w / LP
    q = 1 / (1 / q - 1 / F1)        # 动镜
    q = q + s                       # 镜间距
    q = 1 / (1 / q - 1 / F2)        # 定镜
    return q

def waist_after_f2(s):
    q = q_after(s)
    zw = -q.real                    # 束腰在定镜之后 zw 处
    zr = q.imag
    return zw, zr

def w_at(s, z):
    """定镜之后 z 处的光束半径"""
    q = q_after(s) + z
    inv = 1 / q
    return math.sqrt(-LP / (math.pi * inv.imag))

def solve_s(L):
    """找镜间距 s，使束腰落在 振镜 + L 处"""
    target = G + L
    lo, hi = S0 + 1e-6, S0 + 30
    for _ in range(200):
        mid = (lo + hi) / 2
        zw, _ = waist_after_f2(mid)
        if zw > target: lo = mid    # 间距越大，聚焦越近
        else: hi = mid
    return (lo + hi) / 2

rows = []
for L in [L_MIN, 750, 1000, 1500, L_MAX, L_MAX / math.cos(THETA)]:
    s = solve_s(L)
    zw, zr = waist_after_f2(s)
    w0 = math.sqrt(zr * LP / math.pi)
    d_lens2 = 2 * w_at(s, 0)
    d_galvo = 2 * w_at(s, G)
    # 灵敏度：镜间距变化 → 焦点移动
    ds = 1e-4
    sens = (waist_after_f2(s - ds)[0] - waist_after_f2(s + ds)[0]) / (2 * ds)
    rows.append(dict(L=L, s=s, delta=s - S0, spot=2 * w0 * 1000, dof=0.458 * zr,
                     d2=d_lens2, dg=d_galvo, sens=sens, err=sens * LENS_ERR))

travel = rows[0]["delta"] - rows[-1]["delta"]
# 动镜速度需求：在 L_MIN、扫到边上时，焦点距离变化率 ≈ tanθ·v_spot
dLdt = math.tan(THETA) * SPOT_V
v_lens = dLdt / rows[0]["sens"]

out = []
out.append("# 前聚焦一阶计算结果\n")
out.append(f"> 由 `工具/前聚焦一阶计算.py` 自动生成（{datetime.date.today()}）。薄透镜 + 高斯光束 ABCD，**不含像差**，只用来定方向。\n")
out.append("## 输入\n")
out.append(f"| 参数 | 值 |\n|---|---|\n| 波长 / M² | {LAM*1e6:.0f} nm / {M2} |\n| 激光出光直径 | {D_LASER} mm【假设】 |\n| 固定扩束 | ×{EXP_FIX} |\n| 动镜 f1 / 定镜 f2 | {F1} / {F2} mm（模块扩束 ×{F2/abs(F1):.1f}）|\n| 定镜 → 振镜 | {G} mm【假设】 |\n| 振镜口径 | {APERTURE} mm |\n| 工作距离（振镜 → 目标） | {L_MIN/1000:g} – {L_MAX/1000:g} m【假设】 |\n| 单边扫描角 | ±{math.degrees(THETA):.0f}° |\n")
out.append("## 结果\n")
out.append("| 对焦距离 | 镜间距偏移 δ | 光斑 1/e² | 焦深 ± | 定镜处光束 | 振镜处光束 | 口径余量 | 焦点/δ 倍率 | 0.5 μm 镜片误差 → 焦点 |\n|---|---|---|---|---|---|---|---|---|")
for r in rows:
    tag = "（远端边缘 L/cosθ）" if r is rows[-1] else ""
    out.append(f"| {r['L']/1000:.2f} m{tag} | {r['delta']:.3f} mm | {r['spot']:.0f} μm | {r['dof']:.2f} mm | {r['d2']:.1f} mm | {r['dg']:.1f} mm | ×{APERTURE/r['dg']:.2f} | {r['sens']:.0f} | {r['err']:.3f} mm（占焦深 {r['err']/r['dof']*100:.1f}%） |")
out.append("")
out.append("## 结论\n")
out.append(f"- **动镜行程**（近端中心 → 远端边缘）：**{travel:.2f} mm**，建议机械行程留到 **{math.ceil(travel*1.5)} mm**（余量 50%）")
out.append(f"- **振镜口径**：振镜处光束最大 {max(r['dg'] for r in rows):.1f} mm，口径 {APERTURE} mm，余量 ×{APERTURE/max(r['dg'] for r in rows):.2f}（经验要求 ≥ 1.4）")
out.append(f"- **动镜速度需求**：在 {L_MIN/1000:g} m、光点 {SPOT_V/1000:g} m/s 扫到边上时，约 **{v_lens:.1f} mm/s**，上限 {LENS_VMAX} mm/s 的 {v_lens/LENS_VMAX*100:.0f}%。可见速度不是瓶颈，**延迟才是**（要做提前量补偿）")
out.append(f"- **精度**：0.5 μm 镜片误差占焦深的比例在各个距离下基本相同（第 04 课的结论）")
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "前聚焦一阶计算结果.md")
open(path, "w").write("\n".join(out) + "\n")
print("\n".join(out))
