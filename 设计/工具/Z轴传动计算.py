"""
Z 轴传动设计计算（v0.4）：像机械设计师一样，把 Z 轴每个零件“够不够、会不会出问题”逐项校核。
输入：结构参数.json（尺寸）、Z轴运动质量.json（由 生成CAD.py 按零件体积 × 密度算出）
输出：Z轴传动计算结果.md、Z轴传动计算.json（给课件）
数字来源：【CAD】= 从模型算；【推算】= 本脚本计算；【假设】= 典型值，选型后用真实规格书替换
运行：python Z轴传动计算.py
"""
import json, os, math
here = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(here, "结构参数.json"), encoding="utf-8")); P = D["P"]
M = json.load(open(os.path.join(here, "Z轴运动质量.json"), encoding="utf-8"))
F2 = 150.0; g = 9.81
R = []                                                         # (分组, 项目, 数值, 判据, 结论, 来源)
def row(grp, k, v, crit, ok, src): R.append((grp, k, v, crit, "✓" if ok else "✗", src))

# —— 输入 ——
lead = P["LEAD"] / 1000; d = P["SCREW_D"] / 1000; d2 = d - 0.5 * lead          # 30° 梯形牙中径 ≈ d − 0.5P
spr = P["STEPS"] * P["MICRO"]
m = M["total_g"] / 1000                                                          # 【CAD】运动质量
travel = F2**2 * (1 / 5000 - 1 / 50000)                                          # 4.05 mm
tol50 = 50.0                                                                     # μm，50 m 处容差（需求落地计算.py，f2 = 150）
# 【假设】典型值
T_hold = 0.060      # N·m，NEMA 11 28×32 保持力矩（规格书常见 4–9 N·cm）
J_rot = 9e-7        # kg·m²，转子惯量（常见 9 g·cm²）
pull_ratio = 0.5    # 600 rpm 时可用力矩 ≈ 保持力矩的一半（矩频曲线）
mu = 0.10           # POM 螺母对不锈钢丝杠的摩擦系数（干摩擦 0.1–0.2，取偏小 = 偏危险）
F_pre = 5.0         # N，消隙弹簧预紧力
F_seal = 0.3        # N，滑块密封 + 预压的阻力
T_brg = 3 * 0.05e-3 # N·m，三只 694 轴承的摩擦力矩
k_cpl = 20.0        # N·m/rad，波纹管联轴器扭转刚度
rps = 10.0; t_acc = 0.05                                                         # 10 圈/秒（600 rpm），50 ms 加速

# 1 分辨率
step_um = P["LEAD"] / spr * 1000
row("精度", "一步走多少", f"{step_um:.2f} μm", f"≪ 50 m 处容差 ±{tol50:.0f} μm", step_um < tol50 / 20, "【推算】导程 / (200×16)")
# 2 速度
v = rps * lead; t_full = travel / 1000 / v + t_acc
row("速度", "5 m ↔ 50 m 全程", f"{t_full:.2f} s", "设一次距离：< 1 s 即可", t_full < 1, "【推算】600 rpm + 50 ms 加速")
# 3 轴向力
a = v / t_acc; F_ax = m * a + F_seal
row("受力", "推动滑座要多大力", f"{F_ax:.2f} N", "—", True, f"【推算】运动质量 {M['total_g']:.0f} g【CAD】")
# 4 力矩
lam = math.atan(lead / (math.pi * d2)); mu_e = mu / math.cos(math.radians(15)); phi = math.atan(mu_e)
eta = math.tan(lam) / math.tan(lam + phi)
T_load = F_ax * lead / (2 * math.pi * eta)
T_preld = F_pre * mu_e * d2                                                       # 两个半螺母被弹簧顶开 → 两侧摩擦
J_scr = math.pi * 7850 * (P["SCREW_TH1"] - P["SCREW_TH0"]) / 1000 * d**4 / 32
J_lin = m * (lead / (2 * math.pi))**2
T_acc = (J_rot + J_scr + J_lin) * (2 * math.pi * rps / t_acc)
T_need = T_load + T_preld + T_brg + T_acc; T_av = T_hold * pull_ratio; SF = T_av / T_need
row("受力", "电机要出的力矩", f"{T_need*1000:.1f} mN·m", f"可用约 {T_av*1000:.0f} mN·m，安全系数 ≥ 2", SF >= 2,
    f"【推算】其中消隙预紧 {T_preld*1000:.1f}、加速 {T_acc*1000:.1f}、推力 {T_load*1000:.2f}")
row("受力", "力矩安全系数", f"{SF:.1f}", "≥ 2", SF >= 2, "【推算】")
# 5 自锁
lam_d, phi_d = math.degrees(lam), math.degrees(phi)
row("断电", "导程 1 mm 会不会被推回去", f"螺旋角 {lam_d:.1f}° < 摩擦角 {phi_d:.1f}°", "螺旋角 < 摩擦角 → 自锁", lam_d < phi_d, "【推算】μ = 0.10【假设】")
lam4 = math.degrees(math.atan(4 / 1000 / (math.pi * (d - 0.002))))
row("断电", "对比：导程 4 mm", f"螺旋角 {lam4:.1f}° > 摩擦角 {phi_d:.1f}°", "不自锁 → 断电要靠电机保持", False, "【推算】（说明为什么不选大导程）")
# 6 回差
row("间隙", "螺母回差", "0（弹簧预紧）", f"预紧力 {F_pre:.0f} N > 最大推力 {F_ax:.2f} N", F_pre > 2 * F_ax, "【假设】预紧力；消隙螺母")
wind = T_need / k_cpl * P["LEAD"] / (2 * math.pi) * 1000
row("间隙", "联轴器扭转变形 → 位置误差", f"{wind:.2f} μm", f"≪ ±{tol50:.0f} μm", wind < 1, "【推算】k = 20 N·m/rad【假设】")
# 7 丝杠稳定
L_un = (P["SB_X0"] + P["SB_L"] / 2 - (P["FB_X0"] + P["FB_L"] / 2)) / 1000
dr = d - lead; I = math.pi * dr**4 / 64; A_ = math.pi * dr**2 / 4; E = 193e9; rho = 7900
n_cr = (3.927**2 / (2 * math.pi * L_un**2)) * math.sqrt(E * I / (rho * A_)) * 60
row("丝杠", "临界转速（固定—支撑）", f"{n_cr:,.0f} rpm", "≫ 600 rpm", n_cr > 10 * 600, f"【推算】跨距 {L_un*1000:.0f} mm")
P_cr = math.pi**2 * E * I / (0.7 * L_un)**2
row("丝杠", "压杆失稳力", f"{P_cr:,.0f} N", f"≫ {F_ax + F_pre:.1f} N", P_cr > 100 * (F_ax + F_pre), "【推算】")
# 8 热
d_th = (23.6e-6 - 17.3e-6) * 25 * 10 * 1000
row("温度", "丝杠和铝底座热胀差（10 K）", f"{d_th:.1f} μm", "支撑端浮动吸收；≪ 容差", d_th < 10, "【推算】不锈钢 17.3 / 铝 23.6 ×10⁻⁶/K")
d_obj = 23.6e-6 * (F2 - 30) * 10 * 1000
row("温度", "动镜—物镜距离热胀（10 K）", f"{d_obj:.0f} μm", f"< ±{tol50:.0f} μm；温度传感器可补偿", d_obj < tol50, "【推算】铝底座 120 mm")
# 9 行程 / 原点
row("行程", "工作行程（5–50 m）", f"{travel:.2f} mm", "滑座 X 91.5–95.6", True, "【推算】f2² (1/5 m − 1/50 m)")
hw_flag = 3.0                                                                    # 挡光片半宽
g_home = P["XL_5M"] - (P["HOME_X"] + hw_flag); g_lim = (P["LIMIT_X"] - hw_flag) - P["XL_50M"]
row("行程", "原点 / 限位到工作区", f"{g_home:.1f} / {g_lim:.1f} mm", "> 1 mm：开关不会在工作区内误触发", min(g_home, g_lim) > 1, "【CAD】HOME_X / LIMIT_X、挡光片宽 6")
row("行程", "硬限位到工作区", f"{P['XL_5M'] - (P['STOP_REAR'] + P['CAR_L']/2):.1f} / {(P['STOP_FRONT'] - P['CAR_L']/2) - P['XL_50M']:.1f} mm", "开关失效时最后一道保护", True, "【CAD】")

out = dict(rows=[dict(grp=a, k=b, v=c, crit=e, ok=f, src=s_) for a, b, c, e, f, s_ in R], mass_g=M["total_g"], step_um=step_um,
           t_full=t_full, T_need_mNm=T_need * 1000, SF=SF, lam=lam_d, phi=phi_d, lam4=lam4, travel=travel)
json.dump(out, open(os.path.join(here, "Z轴传动计算.json"), "w"), ensure_ascii=False, indent=1)
md = ["# Z 轴传动设计计算（v0.4，自动生成）\n", "> 由 `工具/Z轴传动计算.py` 生成。【CAD】从模型算；【推算】脚本计算；【假设】典型值，选型后换成规格书数据。\n",
      "| 分组 | 项目 | 结果 | 判据 | 结论 | 来源 |", "|---|---|---|---|---|---|"]
md += [f"| {a} | {b} | {c} | {e} | {f} | {s_} |" for a, b, c, e, f, s_ in R]
md += ["", "注：“导程 4 mm”一行是对比项，✗ 表示它不自锁，所以不选。"]
open(os.path.join(here, "Z轴传动计算结果.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
bad = [r for r in R if r[4] == "✗" and "对比" not in r[1]]
print(f"校核 {len(R)} 项，不通过 {len(bad)} 项；运动质量 {M['total_g']} g；力矩 {T_need*1000:.1f} mN·m，安全系数 {SF:.1f}；全程 {t_full:.2f} s")
