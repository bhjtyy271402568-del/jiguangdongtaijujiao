"""
915 nm 动态聚焦可行性评估（老师需求：工作距离 1–10 m；模型不改，只评估）
输入：结构参数.json（f2、动镜位置、硬限位、出光口径按 20 mm）
输出：915nm评估结果.md
来源标注：【资料】光纤参数为常见规格；【推算】本脚本计算；【假设】未定的量
"""
import json, os, math
here = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(here, "结构参数.json"), encoding="utf-8")); P = D["P"]; F2 = D["f2"]
LAM = 0.915e-6; DOUT = 0.020                                   # 出光口径 20 mm（方案 A，30 mm 振镜）
DIST = [1, 2, 3, 5, 10]
SRC = [("单模半导体（低功率）", None, None, 1.2),
       ("50 μm / NA 0.15 光纤耦合", 50, 0.15, None),
       ("105 μm / NA 0.15 光纤耦合", 105, 0.15, None),
       ("105 μm / NA 0.22 光纤耦合（最常见）", 105, 0.22, None),
       ("200 μm / NA 0.22 光纤耦合（大功率）", 200, 0.22, None)]
def m2(core, na, m): return m if m else (core / 2 * na) / (LAM * 1e6 / math.pi)     # BPP(mm·mrad) ÷ (λ/π)
def spot(M2, L, Dm=DOUT): return 4 * M2 * LAM * L / (math.pi * Dm)
def dof(M2, d): zr = math.pi * (d / 2) ** 2 / (M2 * LAM); return 0.458 * zr        # 光斑变大 10% 的半宽
md = ["# 915 nm 动态聚焦评估（1–10 m，自动生成）\n",
      "> 由 `工具/915nm评估.py` 生成。出光口径 20 mm（现方案）；光斑 = 4M²λL/(πD)（远场近似）；焦深 = ±0.458 z_R（光斑变大 10%）。光纤参数为常见规格，M² = BPP ÷ (λ/π)【推算】。\n",
      "## 1. 不同 915 nm 光源在各距离的光斑（直径）\n",
      "| 光源 | BPP (mm·mrad) | M² | " + " | ".join(f"{L} m" for L in DIST) + " |", "|---|---|---|" + "---|" * len(DIST)]
rows = []
for name, core, na, mm in SRC:
    M2 = m2(core, na, mm); bpp = M2 * LAM * 1e6 / math.pi
    md.append(f"| {name} | {bpp:.1f} | {M2:.0f} | " + " | ".join(f"{spot(M2, L)*1000:.2f} mm" if spot(M2, L) < 0.01 else f"{spot(M2, L)*1000:.0f} mm" for L in DIST) + " |")
    rows.append((name, M2))
md += ["", "## 2. 焦深（光斑基本不变的前后范围）\n", "| 光源 | 1 m 处 | 3 m 处 | 10 m 处 |", "|---|---|---|---|"]
for name, M2 in rows:
    md.append(f"| {name} | ±{dof(M2, spot(M2, 1))*1000:.0f} mm | ±{dof(M2, spot(M2, 3))*1000:.0f} mm | ±{dof(M2, spot(M2, 10)):.1f} m |")
# 行程
dl = lambda L, f2=F2: f2 ** 2 / (L * 1000)                     # 动镜离“对焦无穷远”位置后退 mm
need = dl(1) - dl(10)
car = P["CAR_L"] / 2; xmin = P["STOP_REAR"] + car; xmax = P["STOP_FRONT"] - car
dmax = P["X_L1_INF"] - xmin; Lmin = F2 ** 2 / dmax / 1000
md += ["", "## 3. 现在的结构够不够（模型不改）\n",
       f"- 对焦 1 m 时动镜要后退 {dl(1):.1f} mm，10 m 时 {dl(10):.2f} mm → 1–10 m 需要行程 **{need:.1f} mm**（现在 5–50 m 只要 4.05 mm）【推算】",
       f"- 现在硬限位之间滑座可走 X {xmin:.1f}–{xmax:.1f}，最多后退 {dmax:.1f} mm → 最近只能对焦到约 **{Lmin:.1f} m**；**1–{Lmin:.1f} m 够不着**",
       "- 两种改法（以后再改模型）：", "",
       "| 改法 | 1–10 m 行程 | 代价 |", "|---|---|---|"]
md.append(f"| A：加长行程（f2 仍 150） | {need:.1f} mm | 导轨 55 → 约 75 mm、丝杠加长、限位外移；1 m 端全程约 {need/10+0.05:.1f} s（10 mm/s） |")
for f2 in (100, 75):
    fit = "现有硬限位够用" if dl(1, f2) <= dmax else f"1 m 端要后退 {dl(1, f2):.1f} mm，比现有 {dmax:.0f} mm 多一点，限位要外移"
    md.append(f"| B：物镜换短焦 f2 = {f2}（动镜 f1 = −{f2/5:.0f}，仍 5 倍、20 mm 出光） | {dl(1, f2)-dl(10, f2):.1f} mm | {fit}；两镜间距 {F2 - F2/5:.0f} → {f2 - f2/5:.0f} mm，物镜要前移；镜片更“猛”、像差变大，要用 Zemax 核对 |")
md += ["", "## 4. 其他要换 / 要注意的",
       "- 镀膜：镜片、振镜镜片、保护窗都要 915 nm（或 900–1100 nm 宽带）增透 / 高反",
       "- 焦距随波长略变（色散）→ Z 位置表按 915 nm 重新标定",
       "- 大功率半导体（几十到几百瓦连续）：动镜处 4 mm 光束功率密度高，选熔石英 + 高损伤阈值膜；注意热透镜",
       "- 振镜口径：20 mm 光束配 30 mm 振镜够用；若要更小光斑可把出光加大（光斑 ∝ 1/D），振镜要跟着加大"]
# 5. 反过来：想要多大光斑，激光器 M² 至少要多小（M² ≤ π·D·d / (4·λ·L)）
def m2max(d, L, Dm=DOUT): return math.pi * Dm * d / (4 * LAM * L)
TGT = [(1, 0.5), (1, 1), (1, 2), (10, 1), (10, 2), (10, 5), (10, 10)]
md += ["", "## 5. 想要多大光斑 → 激光器 M² 至少要多小（出光 20 mm）\n", "| 距离 | 光斑要 ≤ | M² 要 ≤ | 相当于 BPP ≤ (mm·mrad) |", "|---|---|---|---|"]
req = []
for L, d in TGT:
    m = m2max(d / 1000, L); req.append(dict(L=L, d=d, m2=round(m, 1), bpp=round(m * LAM * 1e6 / math.pi, 2)))
    md.append(f"| {L} m | {d} mm | {m:.1f} | {m * LAM * 1e6 / math.pi:.2f} |")
md.append(f"\n- 出光口径加大也能缩小光斑：D 20 → 30 mm，光斑 × 0.67（振镜口径要 ≥ 45 mm）")
CURVE_D = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
json.dump(dict(lam_nm=915, D_mm=DOUT * 1000, sources=[dict(name=n, m2=round(m, 1)) for n, m in rows],
               curve=dict(dist=CURVE_D, series=[dict(m2=m, d=[round(spot(m, L) * 1000, 2) for L in CURVE_D]) for m in (1.2, round(m2max(0.005, 10), 1), 40)]),
               req=req, travel=dict(need=round(need, 1), dmax=round(dmax, 1), Lmin=round(Lmin, 1))),
          open(os.path.join(here, "915nm评估.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(here, "915nm评估结果.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(md))
