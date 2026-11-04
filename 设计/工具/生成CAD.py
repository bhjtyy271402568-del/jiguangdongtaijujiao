"""
调焦头详细结构（版本见 结构参数.py 的 VERSION）：读 结构参数.json → STEP（装配体）、GLB（网页 3D）、视图 SVG、BOM
环境：pip install cadquery     运行：python 生成CAD.py
零件节点名 = BOM 编号（英文，便于各 CAD 软件识别）；中文名见 ../CAD/BOM_v<版本>.md
概念详细模型：结构关系、安装方式、调节方式完整；外购件（激光器、振镜、导轨等）为占位外形，选型后替换。
"""
import json, os, re, math
import cadquery as cq
here = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(here, "结构参数.json"), encoding="utf-8"))
P = D["P"]; A = P["AXIS_Z"]; OZ = P["OUT_Z"]; HX, HW, HH, WA = P["HX"], P["HW"], P["HH"], P["WALL"]
W = lambda: cq.Workplane("XY")
def box(x0, x1, y0, y1, z0, z1):
    return W().box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
def cyl(d, L, c, axis="X"):
    wp = {"X": "YZ", "Y": "XZ", "Z": "XY"}[axis]
    return cq.Workplane(wp).circle(d / 2).extrude(L / 2, both=True).translate(c)
def ring(od, idd, L, c, axis="X"):
    wp = {"X": "YZ", "Y": "XZ", "Z": "XY"}[axis]
    return cq.Workplane(wp).circle(od / 2).circle(idd / 2).extrude(L / 2, both=True).translate(c)
def screws(pts, d=5.5, h=3, axis="Z"):
    s = None
    for p in pts:
        c = cyl(d, h, p, axis); s = c if s is None else s.union(c)
    return s

GC = {"H": (.70, .74, .78, 1), "I": (.86, .30, .30, 1), "Z": (.95, .60, .20, 1), "O": (.30, .60, .85, 1),
      "G": (.40, .45, .52, 1), "W": (.45, .75, .95, 1), "E": (.20, .55, .35, 1), "R": (1, .2, .2, .45)}
GLASS = (.55, .80, .98, .55)
V = P["VERSION"]
assy = cq.Assembly(name="FocusHead_v" + V.replace(".", "_"))
SHP = {}                                                                       # 零件形状登记（导出 Z 轴子装配、算质量用）
def add(pid, shape, color=None):
    g = pid[0]; col = color or GC.get(g, (.6, .6, .6, 1)); SHP[pid] = (shape, col)
    assy.add(shape, name=pid, color=cq.Color(*col))
def sphere(r, c): return cq.Workplane().sphere(r).translate(c)
def coil(x0, x1, y, z, R, wr, pitch):
    """沿 X 的弹簧，用一叠细圆环示意（真螺旋扫掠的网格太大，网页 3D 加载慢）"""
    s = None; n = max(2, int((x1 - x0 - 2 * wr) / pitch) + 1); p = (x1 - x0 - 2 * wr) / (n - 1)
    for k in range(n):
        r = ring(2 * (R + wr), 2 * (R - wr), wr * 2, (x0 + wr + k * p, y, z)); s = r if s is None else s.union(r)
    return s

# ================= H 壳体 =================
fl = P["FLOOR"]; lid = P["LID"]; px = P["PART_X"]; iy = HW / 2 - WA; ix0, ix1 = WA, HX - WA
base = box(0, HX, -HW / 2, HW / 2, 0, HH - lid).cut(box(ix0, ix1, -iy, iy, fl, HH))
base = base.union(box(px, px + 6, -iy, iy, fl, HH - lid))                     # 隔断
base = base.cut(cyl(24, 30, (WA / 2, 0, A)))                                   # 入光孔
base = base.cut(cyl(34, 20, (px + 3, 0, A)))                                   # 隔断通光孔
base = base.cut(cyl(P["WIN_D"] - 4, 20, (P["GAL_X"], HW / 2 - WA / 2, OZ), "Y"))  # 侧面出光孔
base = base.cut(box(-1, WA + 1, 45 - 20, 45 + 20, 95 - 6, 95 + 6))            # DB25 开口
base = base.cut(cyl(16, 20, (WA / 2, 55, 30)))                                 # 电源插座孔
base = base.cut(cyl(8, 20, (WA / 2, -50, 95)))                                 # 透气阀孔
# 密封槽：离内壁 0.7–2.5 mm，深 1.5
gz = HH - lid
groove = box(ix0 - 2.5, ix1 + 2.5, -iy - 2.5, iy + 2.5, gz - 1.5, gz + 1).cut(box(ix0 - 0.7, ix1 + 0.7, -iy - 0.7, iy + 0.7, gz - 2, gz + 2))
base = base.cut(groove)
# 上盖螺钉：在墙体中间（离内壁 4 mm）
yS = iy + 4
lid_pts = [(x, y) for x in (40, 130, 200, 290, 340) for y in (-yS, yS)] + [(ix0 - 4, -40), (ix0 - 4, 40), (ix1 + 4, -40), (ix1 + 4, 40)]
for (x, y) in lid_pts: base = base.cut(cyl(2.5, 14, (x, y, HH - lid - 6), "Z"))
add("H01_Base", base)
lidp = box(0, HX, -HW / 2, HW / 2, HH - lid, HH)
for (x, y) in lid_pts: lidp = lidp.cut(cyl(3.4, lid + 2, (x, y, HH - lid / 2), "Z"))
add("H02_Lid", lidp)
add("H03_LidScrews", screws([(x, y, HH + 1.5) for (x, y) in lid_pts]), (.25, .25, .28, 1))
add("H06_LidGasket", box(ix0 - 2.3, ix1 + 2.3, -iy - 2.3, iy + 2.3, gz - 1.4, gz).cut(box(ix0 - 0.9, ix1 + 0.9, -iy - 0.9, iy + 0.9, gz - 2, gz + 1)), (.08, .08, .08, 1))
add("H05_Breather", cyl(12, 10, (-5, -50, 95)).union(cyl(16, 3, (-1.5, -50, 95))), (.15, .15, .17, 1))
# 散热鳍片（振镜驱动板下方，底板外）
gx = P["GAL_X"]
hs = box(gx + 32, gx + 80, -76, 76, -3, 0)
for k in range(9):
    yy = -72 + k * 18
    hs = hs.union(box(gx + 32, gx + 80, yy - 1.2, yy + 1.2, -15, -3))
add("H07_HeatSink", hs, (.55, .58, .62, 1))
# ================= I 激光输入 =================
cx0 = P["COLL_X0"]; cl = P["COLL_L"]
add("I01_Collimator", cyl(P["COLL_D"], cl, (cx0 + cl / 2, 0, A)).union(cyl(P["COLL_D"] - 6, 10, (cx0 + cl + 5, 0, A))), (.85, .25, .25, 1))
add("I02_FiberCable", cyl(8, 60, (cx0 - 30, 0, A)), (.15, .15, .18, 1))
fT = P["FLANGE_T"]
add("I03_TiltFlange", ring(P["FLANGE_OD"], P["COLL_D"] + 1, fT, (-fT / 2, 0, A)).cut(box(-fT - 1, 1, -3, 3, A + 8, A + 40)))
add("I05_TiltScrews", screws([(-fT - 2.5, 26 * math.cos(a), A + 26 * math.sin(a)) for a in (math.pi / 2, math.pi * 7 / 6, math.pi * 11 / 6)], 7, 5, "X"), (.25, .25, .28, 1))
cL = P["CLAMP_L"]
add("I04_Clamp", ring(P["CLAMP_OD"], P["COLL_D"], cL, (-fT - cL / 2, 0, A)).cut(box(-fT - cL - 1, -fT + 1, -1, 1, A, A + 30)))
ax = P["APER_X"]
add("I06_Aperture", ring(P["APER_OD"], P["APER_ID"], 6, (ax, 0, A)).union(box(ax - 3, ax + 3, -10, 10, fl, A - P["APER_OD"] / 2 + 1)), (.80, .50, .25, 1))
if P["RED_COMBINER"]:
    cbx = P["COMB_X"]
    add("I07_Combiner", cyl(P["COMB_D"], 3, (0, 0, 0)).rotate((0, 0, 0), (0, 0, 1), -45).translate((cbx, 0, A)), GLASS)
    cm = ring(36, 24, 6, (0, 0, 0)).rotate((0, 0, 0), (0, 0, 1), -45).translate((cbx - 3.9, 3.9, A))
    add("I08_CombMount", cm.union(box(cbx - 9, cbx + 1, -2, 12, fl, A - 17)), (.25, .27, .30, 1))
    add("I09_RedModule", cyl(P["RED_D"], P["RED_L"], (cbx, P["RED_Y"], A), "Y"), (.95, .40, .40, 1))
    add("I10_RedHolder", box(cbx - 9, cbx + 9, P["RED_Y"] - 7, P["RED_Y"] + 7, fl, A - P["RED_D"] / 2).union(ring(18, P["RED_D"], 10, (cbx, P["RED_Y"], A), "Y")))

# ================= Z 调焦机构（v0.4：传动链按机械设计重做）=================
# 电机 → 波纹管联轴器 → 丝杠（固定端一对轴承背靠背 / 支撑端一只轴承可轴向滑）→ 消隙螺母（两个半螺母 + 弹簧）
# → 螺母支架上的钢球 → 滑块推板（拉簧保持贴紧）→ 滑块（MGN7C）→ 镜座 → 动镜
zt = fl + P["ZB_T"]; zb = box(P["ZB_X0"], P["ZB_X1"], -P["ZB_W"] / 2, P["ZB_W"] / 2, fl, zt)
for x in (P["ZB_X0"] + 8, P["ZB_X1"] - 8):
    for y in (-P["ZB_W"] / 2 + 8, P["ZB_W"] / 2 - 8): zb = zb.cut(cyl(3.4, 20, (x, y, zt), "Z"))
add("Z01_ZBase", zb)
r0 = zt + P["RISER_H"]                                                        # 垫高块顶面
add("Z22_Riser", box(P["RAIL_X0"] - 4, P["RAIL_X1"] + 4, -8, 8, zt, r0))
rt = r0 + P["RAIL_H"]
rail = box(P["RAIL_X0"], P["RAIL_X1"], -P["RAIL_W"] / 2, P["RAIL_W"] / 2, r0, rt)
rhx = [P["RAIL_X0"] + 5 + 15 * k for k in range(4)]                           # 孔距 15，离端 5
for x in rhx: rail = rail.cut(cyl(2.4, 12, (x, 0, rt), "Z")).cut(cyl(4.2, 2.4, (x, 0, rt), "Z"))
add("Z02_Rail", rail, (.55, .57, .60, 1))
add("Z02b_RailScrews", screws([(x, 0, rt - 0.62) for x in rhx], 3.6, 1.1), (.20, .20, .22, 1))
xl = P["X_L1_INF"]; ct = rt + P["CAR_H"]; hw = P["CAR_W"] / 2
def ushape(x0, x1):                                                           # 骑在导轨上的 U 形截面
    return box(x0, x1, -hw, hw, rt - 3, ct).cut(box(x0 - 1, x1 + 1, -P["RAIL_W"] / 2 - 0.1, P["RAIL_W"] / 2 + 0.1, rt - 4, rt))
car = ushape(xl - 10.5, xl + 10.5)
for dx in (-4, 4):
    for dy in (-6, 6): car = car.cut(cyl(1.6, 6, (xl + dx, dy, ct), "Z"))
add("Z03_Carriage", car, (.45, .47, .50, 1))
add("Z03b_EndSeals", ushape(xl - 11.5, xl - 10.5).union(ushape(xl + 10.5, xl + 11.5)), (.70, .15, .15, 1))
# 镜座：底板 + 立板，镜片和螺纹压圈装在立板的台阶孔里
lh = box(xl - 8, xl + 8, -hw, hw, ct, ct + 2.5).union(box(xl - 3, xl + 3, -11, 11, ct, A + 11))
lh = lh.cut(cyl(11, 20, (xl, 0, A))).cut(cyl(P["L1_D"] + 0.2, 4.5, (xl + 0.75, 0, A)))
hp = [(xl + dx, dy) for dx in (-6, 6) for dy in (-5.5, 5.5)]
for (x, y) in hp: lh = lh.cut(cyl(2.2, 6, (x, y, ct + 1.25), "Z"))
add("Z04_LensHolder", lh)
add("Z04b_HolderScrews", screws([(x, y, ct + 3.2) for (x, y) in hp], 3.6, 1.4), (.20, .20, .22, 1))
add("Z05_L1", cyl(P["L1_D"], 3, (xl, 0, A)), GLASS)
add("Z06_L1Ring", ring(12.8, 10, 1.5, (xl + 2.25, 0, A)), (.25, .25, .28, 1))
# 浮动接头：螺母支架上的钢球顶住滑块推板，拉簧让它们始终贴紧
sy, sz = P["SCREW_Y"], P["SCREW_Z"]
add("Z07_CarriageTab", box(xl - 11.5, xl - 9, -14, -hw, sz - 5, ct))
xn = xl - 2.5                                                                 # 螺母法兰端面
nb = box(xn - 2.5, xn, sy - 10, -11, sz - 9, sz + 9).cut(cyl(7, 10, (xn - 1.25, sy, sz)))
for dz in (-7.5, 7.5): nb = nb.cut(cyl(2.2, 10, (xn - 1.25, sy, sz + dz)))
add("Z07b_NutBracket", nb)
add("Z07c_BracketScrews", screws([(xn - 3.25, sy, sz + dz) for dz in (-7.5, 7.5)], 3.6, 1.5, "X"), (.20, .20, .22, 1))
add("Z21_FloatBall", sphere(2, (xl - 7, -13, sz)), (.85, .86, .90, 1))
add("Z21b_PreloadSpring", coil(xl - 9, xl - 5, -12, sz - 3.5, 1.0, 0.2, 0.6), (.60, .62, .66, 1))
# 消隙螺母：外壳（法兰 + 筒）里装半螺母 A、弹簧、半螺母 B
nh = ring(20, 5.4, 3, (xn + 1.5, sy, sz)).union(ring(12, 10.2, 15, (xn + 10.5, sy, sz))).union(ring(12, 5.4, 0.5, (xn + 17.75, sy, sz)))
for dz in (-7.5, 7.5): nh = nh.cut(cyl(2.2, 4, (xn + 1.5, sy, sz + dz)))
add("Z08_NutHousing", nh, (.80, .66, .30, 1))
add("Z08a_HalfNutA", ring(10, P["SCREW_D"], 5.5, (xn + 6.25, sy, sz)), (.95, .95, .92, 1))
add("Z08c_NutSpring", coil(xn + 9, xn + 12, sy, sz, 3.9, 0.3, 0.75), (.60, .62, .66, 1))
add("Z08b_HalfNutB", ring(10, P["SCREW_D"], 5.5, (xn + 14.75, sy, sz)), (.95, .95, .92, 1))
# 丝杠：轴颈 Ø4 | 螺纹 Ø5（每 1 mm 一道槽，示意螺纹）| 轴颈 Ø4
x0s, t0, t1, x1s, J = P["SCREW_X0"], P["SCREW_TH0"], P["SCREW_TH1"], P["SCREW_X1"], P["SCREW_J"]
scr = cyl(J, t0 - x0s, ((x0s + t0) / 2, sy, sz)).union(cyl(P["SCREW_D"], t1 - t0, ((t0 + t1) / 2, sy, sz))).union(cyl(J, x1s - t1, ((t1 + x1s) / 2, sy, sz)))
gr = None
for k in range(int(t1 - t0) - 1):
    r = ring(P["SCREW_D"] + 1, P["SCREW_D"] - 0.6, 0.35, (t0 + 1 + k * P["LEAD"], sy, sz)); gr = r if gr is None else gr.union(r)
add("Z09_Screw", scr.cut(gr), (.75, .75, .78, 1))
def bearing(xc):                                                              # 外圈 + 内圈 + 8 颗钢珠
    b = ring(P["BRG_OD"], P["BRG_OD"] - 1.6, P["BRG_W"], (xc, sy, sz)).union(ring(P["BRG_ID"] + 1.6, P["BRG_ID"], P["BRG_W"], (xc, sy, sz)))
    rm = (P["BRG_OD"] + P["BRG_ID"]) / 4
    for k in range(8):
        a = 2 * math.pi * k / 8; b = b.union(sphere(0.85, (xc, sy + rm * math.cos(a), sz + rm * math.sin(a))))
    return b
def brg_block(x0, L, step):                                                   # 轴承座：带安装脚
    k = box(x0, x0 + L, sy - 10, sy + 10, zt, sz + 10).union(box(x0, x0 + L, sy - 14, sy + 10, zt, zt + 4))
    k = k.cut(cyl(P["BRG_OD"], L - step + 0.01, (x0 + step + (L - step) / 2, sy, sz)))
    if step: k = k.cut(cyl(7, 3 * L, (x0, sy, sz)))
    for x in (x0 + 2.5, x0 + L - 2.5): k = k.cut(cyl(2.4, 20, (x, sy - 12, zt), "Z"))
    return k
f0, fL = P["FB_X0"], P["FB_L"]
add("Z10_BearingFix", brg_block(f0, fL, 1))                                   # 电机侧 1 mm 挡肩
add("Z10d_BearingPair", bearing(f0 + 3).union(bearing(f0 + 7)), (.78, .80, .84, 1))
add("Z10b_LockNut", ring(8, J, 2, (f0 + fL + 1, sy, sz)), (.25, .25, .28, 1))
s0_, sL = P["SB_X0"], P["SB_L"]
add("Z11_BearingSup", brg_block(s0_, sL, 0))
add("Z11b_BearingSup", bearing(s0_ + sL / 2), (.78, .80, .84, 1))
# 联轴器：两端夹紧毂 + 中间波纹
c0, cL, cd = P["CPL_X0"], P["CPL_L"], P["CPL_D"]
cp = ring(cd, 5, 3.5, (c0 + 1.75, sy, sz)).union(ring(cd, J, 3.5, (c0 + cL - 1.75, sy, sz))).union(ring(cd - 2.5, cd - 3.5, cL - 7, (c0 + cL / 2, sy, sz)))
for k in range(5): cp = cp.union(ring(cd, cd - 3, 0.5, (c0 + 4 + k, sy, sz)))
for xc in (c0 + 1.75, c0 + cL - 1.75):
    cp = cp.cut(box(xc - 1.75, xc + 1.75, sy - 0.3, sy + 0.3, sz + 2, sz + 7)).cut(cyl(1.7, 14, (xc, sy, sz + 3.6), "Y"))
add("Z12_Coupling", cp, (.80, .80, .82, 1))
csx = None
for xc in (c0 + 1.75, c0 + cL - 1.75):
    t = cyl(1.6, 10, (xc, sy, sz + 3.6), "Y").union(cyl(2.8, 1.2, (xc, sy + 6.6, sz + 3.6), "Y")); csx = t if csx is None else csx.union(t)
add("Z12b_ClampScrews", csx, (.20, .20, .22, 1))
# 电机 NEMA 11：机身 + 法兰（倒角）+ 止口 + 轴（带削平）+ 接线头
mx = P["MOTOR_X0"]; m = P["MOTOR"]; me = mx + P["MOTOR_L"]
mb = box(mx, me, sy - m / 2, sy + m / 2, sz - m / 2, sz + m / 2).edges("|X").chamfer(2.5)
for k in range(4): mb = mb.cut(ring(m + 2, m - 0.6, 0.6, (mx + 6 + k * 5, sy, sz)))  # 机身分段线
mpts = [(sy + dy, sz + dz) for dy in (-11.5, 11.5) for dz in (-11.5, 11.5)]
for (y, z) in mpts: mb = mb.cut(cyl(2.5, 8, (me, y, z)))
add("Z13_Motor", mb.union(cyl(22, 1.5, (me + 0.75, sy, sz))), (.18, .20, .24, 1))
add("Z13b_MotorShaft", cyl(5, c0 + 3.5 - me - 1.5, ((me + 1.5 + c0 + 3.5) / 2, sy, sz)).cut(box(me + 4, c0 + 4, sy - 3, sy + 3, sz + 2, sz + 3)), (.85, .85, .88, 1))
add("Z13c_MotorConn", box(mx + 3, mx + 13, sy - m / 2 - 4, sy - m / 2, sz - 4, sz + 4), (.92, .92, .90, 1))
mt = P["MM_T"]
mm = box(me, me + mt, sy - 16, sy + 16, zt, sz + 16).cut(cyl(22.2, 10, (me + 2, sy, sz)))
for (y, z) in mpts: mm = mm.cut(cyl(2.7, 10, (me + 2, y, z)))
for y in (sy - 14, sy + 14): mm = mm.cut(cyl(2.4, 16, (me + mt / 2, y, zt), "Z"))   # 底面两个螺纹孔，从 Z 底座下面锁
add("Z14_MotorMount", mm)
add("Z14b_MountScrews", screws([(me + mt + 0.8, y, z) for (y, z) in mpts], 4.4, 1.6, "X"), (.20, .20, .22, 1))
def slot_sensor(x):
    return box(x - 6, x + 6, 10, 22, zt, zt + 14).cut(box(x - 7, x + 7, 14.5, 17.5, zt + 4, zt + 15))
add("Z15_HomeSensor", slot_sensor(P["HOME_X"]), (.15, .15, .17, 1))
add("Z16_LimitSensor", slot_sensor(P["LIMIT_X"]), (.15, .15, .17, 1))
add("Z17_Flag", box(xl - 3, xl + 3, 15.5, 16.5, zt + 6, rt + 4).union(box(xl - 3, xl + 3, hw, 16.5, rt + 2, rt + 4)), (.85, .85, .2, 1))
sr, sf = P["STOP_REAR"], P["STOP_FRONT"]
add("Z23_HardStops", box(sr - 3, sr - 1, 4, 8, r0, rt + 4).union(box(sf + 1, sf + 3, 4, 8, r0, rt + 4)), (.85, .2, .2, 1))
add("Z23b_Bumpers", box(sr - 1, sr, 4, 8, rt - 2, rt + 4).union(box(sf, sf + 1, 4, 8, rt - 2, rt + 4)), (.10, .10, .10, 1))
add("Z24_TransportLock", box(xl + 4, xl + 11, -13.5, -hw, zt, ct).union(cyl(3.6, 1.4, (xl + 7.5, -11, ct + 0.7), "Z")), (.90, .10, .10, 1))
sh = P["SHADE_D"]
add("Z18_ShadeTube", ring(sh, sh - 3, P["SHADE_X1"] - P["SHADE_X0"], ((P["SHADE_X0"] + P["SHADE_X1"]) / 2, 0, A)), (.85, .87, .90, .45))
sad = None
for x in (P["SHADE_X0"] + 15, P["SHADE_X1"] - 13):
    t = box(x - 5, x + 5, -sh / 2 - 1.5, sh / 2 + 1.5, zt, A).cut(cyl(sh, 12, (x, 0, A)))
    sad = t if sad is None else sad.union(t)
add("Z19_ShadeSaddle", sad)
add("Z20_TempSensor", box(P["X_OBJ"] - 30, P["X_OBJ"] - 22, 26, 31, zt, zt + 3), (.1, .5, .3, 1))

# ================= O 物镜组件 =================
xm, s = P["XYM_X0"], P["XYM_S"]; xo = P["X_OBJ"]
xym = box(xm, xm + P["XYM_T"], -s / 2, s / 2, zt, A + s / 2).cut(cyl(P["OBJ_TUBE_OD"] + 4, 20, (xm + P["XYM_T"] / 2, 0, A)))
c = xm + P["XYM_T"] / 2; ro = P["OBJ_TUBE_OD"] / 2
for (dy, dz, ax) in ((0, 1, "Z"), (1, 0, "Y"), (-1, 0, "Y")):          # 三点：两颗调节顶丝 + 一颗弹簧顶销
    xym = xym.cut(cyl(4.2, s / 2 - ro + 4, (c, dy * (ro + s / 2) / 2, A + dz * (ro + s / 2) / 2), ax))
add("O01_XYMount", xym)
add("O02_ObjTube", ring(P["OBJ_TUBE_OD"], P["OBJ_D"], 30, (xo, 0, A)).union(ring(P["OBJ_TUBE_OD"] + 8, P["OBJ_D"], 3, (xm + P["XYM_T"] + 1.5, 0, A))), (.35, .37, .40, 1))
add("O03_Objective", cyl(P["OBJ_D"], 8, (xo, 0, A)), GLASS)
add("O04_ObjRing", ring(P["OBJ_D"] - 0.2, P["OBJ_D"] - 8, 3, (xo + 6, 0, A)), (.25, .25, .28, 1))
cs = None
for (dy, dz, ax) in ((0, 1, "Z"), (1, 0, "Y"), (-1, 0, "Y")):
    L = s / 2 - ro + 2.5; r0 = ro + 0.5 + L / 2
    t = cyl(4, L, (c, dy * r0, A + dz * r0), ax).union(cyl(7, 3, (c, dy * (s / 2 + 2.5), A + dz * (s / 2 + 2.5)), ax))
    cs = t if cs is None else cs.union(t)
add("O05_CenterScrews", cs, (.25, .25, .28, 1))

# ================= G 振镜组件 =================
gx = P["GAL_X"]; by = P["BR_Y"]
br = box(P["BR_X0"], P["BR_X1"], -by, by, P["BR_Z0"], P["BR_Z1"])
br = br.cut(box(gx - 22, gx + 22, -by + 4, by - 4, A - 20, OZ + 21))                 # 镜腔
br = br.cut(cyl(32, 40, (P["BR_X0"] + 10, 0, A)))                               # 入光孔
br = br.cut(cyl(40, 20, (gx, by, OZ), "Y"))                                     # 出光孔
br = br.cut(cyl(10, 20, (gx, -by, A), "Y")).cut(cyl(10, 20, (P["BR_X1"], 0, OZ)))  # 电机轴孔
add("G01_Bracket", br)
gd, gl = P["GAL_D"], P["GAL_L"]
add("G02_MotorX", cyl(gd, gl, (gx, -by - 2 - gl / 2, A), "Y").union(cyl(4, by + 2 - 18, (gx, -(by + 2 + 18) / 2, A), "Y")), (.30, .32, .36, 1))
add("G03_ClampX", ring(gd + 10, gd, 12, (gx, -by - 8, A), "Y").cut(box(gx - 1, gx + 1, -by - 20, -by, A, A + gd)))
add("G04_MirrorX", cq.Workplane("YZ").ellipse(17, 23).extrude(1.5, both=True).rotate((0, 0, 0), (0, 1, 0), 45).translate((gx, 0, A)), (.85, .90, .95, .9))
add("G05_MotorY", cyl(gd, gl, (P["BR_X1"] + 2 + gl / 2, 0, OZ)).union(cyl(4, P["BR_X1"] + 2 - gx - 21, ((gx + 21 + P["BR_X1"] + 2) / 2, 0, OZ))), (.30, .32, .36, 1))
add("G06_ClampY", ring(gd + 10, gd, 12, (P["BR_X1"] + 8, 0, OZ)).cut(box(P["BR_X1"], P["BR_X1"] + 20, -1, 1, OZ, OZ + gd)))
add("G07_MirrorY", cq.Workplane("XY").ellipse(20, 28).extrude(1.5, both=True).rotate((0, 0, 0), (1, 0, 0), 45).translate((gx, 0, OZ)), (.85, .90, .95, .9))
def driver(y0, y1):
    x0, x1 = gx + 32, gx + 80
    b = box(x0, x1, y0, y1, fl + 6, fl + 7.6).union(box(x0 + 14, x1 - 10, (y0 + y1) / 2 - 10, (y0 + y1) / 2 + 10, fl + 7.6, fl + 20))
    for x in (x0 + 4, x1 - 4):
        for y in (y0 + 4, y1 - 4): b = b.union(cyl(5, 6, (x, y, fl + 3), "Z"))
    return b
add("G08_DriverX", driver(-75, -10), (.10, .45, .25, 1))
add("G09_DriverY", driver(10, 75), (.10, .45, .25, 1))
add("G10_ThermalPads", box(gx + 46, gx + 70, -52.5, -32.5, fl, fl + 6).union(box(gx + 46, gx + 70, 32.5, 52.5, fl, fl + 6)), (.85, .55, .75, 1))

# ================= W 保护窗 =================
wy = HW / 2; tl = P["WIN_TILT"]
def tilt(o, c): return o.rotate(c, (c[0] + 1, c[1], c[2]), tl)
wc = (gx, wy + 4.6, OZ)
wf = ring(P["WIN_FR_OD"], P["WIN_D"] - 8, 10, (gx, wy + 5, OZ), "Y").cut(tilt(cyl(P["WIN_D"] + 0.6, 5.2, wc, "Y"), wc)).cut(cyl(P["WIN_D"] - 2, 12, (gx, wy + 5, OZ), "Y")).cut(ring(66.4, 61.6, 3.2, (gx, wy, OZ), "Y"))
add("W01_WinFrame", wf.union(screws([(gx + 33 * math.cos(a), wy + 11.5, OZ + 33 * math.sin(a)) for a in (0.785, 2.356, 3.927, 5.498)], 5.5, 3, "Y")), (.35, .37, .40, 1))
add("W02_Window", tilt(cyl(P["WIN_D"], P["WIN_T"], wc, "Y"), wc), GLASS)
add("W03_ORing", ring(66, 62, 1.5, (gx, wy + 0.75, OZ), "Y"), (.1, .1, .1, 1))
add("W04_AirKnife", box(gx - 10, gx + 10, wy + 4, wy + 14, OZ + 42, OZ + 50).union(cyl(6, 20, (gx - 20, wy + 9, OZ + 46))), (.75, .75, .78, 1))

# ================= E 电子与接口 =================
sd = box(110, 170, iy - 4, iy - 2.4, fl + 8, fl + 58).union(box(130, 150, iy - 14, iy - 4, fl + 20, fl + 40))
for x in (114, 166):
    for z in (fl + 12, fl + 54): sd = sd.union(cyl(5, 2.4, (x, iy - 1.2, z), "Y"))
add("E01_StepDriver", sd, (.10, .45, .25, 1))
add("E02_DB25", box(-8, 0, 45 - 26.5, 45 + 26.5, 95 - 9, 95 + 9).union(box(-14, -8, 45 - 20, 45 + 20, 95 - 6, 95 + 6)), (.75, .75, .78, 1))
add("E03_PowerConn", cyl(20, 16, (-8, 55, 30)).union(cyl(26, 3, (-1.5, 55, 30))), (.30, .30, .32, 1))
add("E04_GroundStud", cyl(4, 12, (-6, 70, 18)), (.80, .65, .20, 1))

# ================= 安装接口板：按重心自动放置 =================
_c = assy.toCompound(); com = cq.Shape.centerOfMass(_c)
cx_, cy_ = round(com.x / 5) * 5, round(com.y / 5) * 5
mp = box(cx_ - 45, cx_ + 45, cy_ - 45, cy_ + 45, -8, 0)
for (dx, dy) in ((-30, -30), (-30, 30), (30, -30), (30, 30)): mp = mp.cut(cyl(6.6, 12, (cx_ + dx, cy_ + dy, -4), "Z"))
for (dx, dy) in ((-38, 0), (38, 0)): mp = mp.cut(cyl(6, 12, (cx_ + dx, cy_ + dy, -4), "Z"))
add("H04_MountPlate", mp)
COM = (com.x, com.y, com.z)

# ================= 参考光束（不属于零件）=================
assy.add(cyl(4, xl - cx0 - cl - 10, ((cx0 + cl + 10 + xl) / 2, 0, A)), name="R01_Beam", color=cq.Color(*GC["R"]))
assy.add(cq.Workplane().add(cq.Solid.makeCone(2, 10.5, xo - xl, cq.Vector(xl, 0, A), cq.Vector(1, 0, 0))), name="R02_BeamExpand", color=cq.Color(*GC["R"]))
assy.add(cyl(21, gx - xo, ((gx + xo) / 2, 0, A)), name="R03_Beam20", color=cq.Color(*GC["R"]))
assy.add(cyl(20, OZ - A, (gx, 0, (A + OZ) / 2), "Z"), name="R04_BeamUp", color=cq.Color(*GC["R"]))
assy.add(cyl(20, wy + 80, (gx, (wy + 80) / 2, OZ), "Y"), name="R05_BeamOut", color=cq.Color(*GC["R"]))

# ================= 输出 =================
out = os.path.join(here, "..", "CAD"); os.makedirs(out, exist_ok=True)
# Z 轴子装配（给课件 3D 用）：Z 零件 + 物镜组件 + 两段光束。先导出它：网格会被缓存，整机 GLB 也沿用这个精度
za = cq.Assembly(name="Z_Axis_v" + V.replace(".", "_"))
for pid, (shp, col) in SHP.items():
    if pid[0] == "Z" or pid.startswith("O0"): za.add(shp, name=pid, color=cq.Color(*col))
za.add(cyl(4, xl - P["APER_X"], ((P["APER_X"] + xl) / 2, 0, A)), name="R01_Beam", color=cq.Color(*GC["R"]))
za.add(cq.Workplane().add(cq.Solid.makeCone(2, 10.5, xo - xl, cq.Vector(xl, 0, A), cq.Vector(1, 0, 0))), name="R02_BeamExpand", color=cq.Color(*GC["R"]))
za.export(os.path.join(out, f"z_axis_v{V}.glb"), "GLTF", tolerance=0.05, angularTolerance=0.3)
assy.export(os.path.join(out, f"调焦头_v{V}.step"))
assy.export(os.path.join(out, f"focus_head_v{V}.glb"), "GLTF", tolerance=0.08, angularTolerance=0.15)
# 运动部分质量（体积 × 密度）→ Z轴运动质量.json（给 Z轴传动计算.py）
RHO = {"Z03_Carriage": 7.85, "Z03b_EndSeals": 1.2, "Z04_LensHolder": 2.7, "Z04b_HolderScrews": 7.85, "Z05_L1": 2.2, "Z06_L1Ring": 2.7,
       "Z07_CarriageTab": 2.7, "Z07b_NutBracket": 2.7, "Z07c_BracketScrews": 7.85, "Z21_FloatBall": 7.85, "Z21b_PreloadSpring": 7.85,
       "Z08_NutHousing": 8.5, "Z08a_HalfNutA": 1.41, "Z08b_HalfNutB": 1.41, "Z08c_NutSpring": 7.85, "Z17_Flag": 2.7}
def vol(w): return sum(v.Volume() for v in (w.vals() if hasattr(w, "vals") else [w]))
mass = {k: round(vol(SHP[k][0]) * RHO[k] / 1000, 2) for k in RHO}
json.dump(dict(moving_g=mass, total_g=round(sum(mass.values()), 1), rho_g_cm3=RHO), open(os.path.join(here, "Z轴运动质量.json"), "w"), ensure_ascii=False, indent=1)
print("Z 轴运动部分质量", round(sum(mass.values()), 1), "g")
comp = assy.toCompound()
def view(name, d):
    p = os.path.join(out, f"调焦头_v0.2_{name}.svg")
    cq.exporters.export(cq.Workplane().add(comp), p, opt={"width": 1100, "height": 560, "marginLeft": 30, "marginTop": 30,
        "projectionDir": d, "showAxes": False, "strokeWidth": 0.35, "strokeColor": (40, 45, 55), "showHidden": False})
    t = open(p, encoding="utf-8").read()
    h = float(re.search(r'<svg[^>]*height="([0-9.]+)', t).group(1))
    t = re.sub(r'(<svg[^>]*>)', r'\1<rect width="100%%" height="100%%" fill="#ffffff"/><g transform="translate(0,%g) scale(1,-1)">' % h, t, count=1).replace("</svg>", "</g></svg>")
    open(p, "w", encoding="utf-8").write(t)
# 视图图片改由网页 3D 渲染（见 学习推进记录/图/08b-*.png、CAD/*.png）；CadQuery 线框投影方向不可控，暂不用
# view("轴测", (1.0, -1.4, 1.0))
# BOM
names = {b["id"]: b for b in D["bom"]}
md = [f"# 调焦头 v{V} 零件清单（BOM）\n", "> 由 `工具/生成CAD.py` 生成。编号 = STEP / GLB 里的零件节点名。“做” = 自制件，“买” = 外购件。\n",
      "| 编号 | 子系统 | 名称 | 数量 | 规格 / 说明 | 做/买 | 参考 |\n|---|---|---|---|---|---|---|"]
for b in D["bom"]: md.append(f"| {b['id']} | {D['groups'][b['g']]} | {b['name']} | {b['qty']} | {b['spec']} | {b['make']} | {b['ref']} |")
mk = sum(1 for b in D["bom"] if b["make"] == "做"); md.append(f"\n共 {len(D['bom'])} 种：自制 {mk} 种，外购 {len(D['bom']) - mk} 种。")
open(os.path.join(out, f"BOM_v{V}.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
bb = comp.BoundingBox()
print(f"完成 v{V}：{len(D['bom'])} 种零件；包络 {bb.xlen:.0f} × {bb.ylen:.0f} × {bb.zlen:.0f} mm；重心 ({COM[0]:.0f}, {COM[1]:.0f}, {COM[2]:.0f})")
