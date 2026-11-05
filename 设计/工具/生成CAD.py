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

# ================= Z 调焦机构（v0.8：在用户 v0.7 基础上精修）=================
# 电机 → 波纹管联轴器 → 丝杠（固定端：一体支座的轴承室，挡肩 + 端盖夹外圈、台阶 + 锁紧螺母夹内圈；支撑端：带底脚轴承座，外圈可滑）
# → 消隙螺母 → 钢球浮动接头 → MGN7C 滑块 → 墓碑形镜座 → 动镜。配色：黑色阳极氧化结构件 + 银色钢件 + 黄铜螺母 + 喷砂铝底座
BLK, STL, ALU, BRS = (.22, .23, .26, 1), (.74, .76, .79, 1), (.70, .72, .75, 1), (.80, .66, .30, 1)
def cham(w, r=0.6, sel=None):
    try: return w.edges(sel).chamfer(r) if sel else w.edges().chamfer(r)
    except Exception: return w
def boxc(x0, x1, y0, y1, z0, z1, r=0.6):                                  # 带倒角的方块
    return cham(W().box(x1 - x0, y1 - y0, z1 - z0), r).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
zt = fl + P["ZB_T"]; sy, sz = P["SCREW_Y"], P["SCREW_Z"]; m = P["MOTOR"]; mx = P["MOTOR_X0"]; me = mx + P["MOTOR_L"]
zb = W().box(P["ZB_X1"] - P["ZB_X0"], P["ZB_W"], P["ZB_T"])
try: zb = zb.edges("|Z").fillet(4).edges(">Z").chamfer(1)
except Exception: pass
zb = zb.translate(((P["ZB_X0"] + P["ZB_X1"]) / 2, 0, fl + P["ZB_T"] / 2))
for x in (P["ZB_X0"] + 8, P["ZB_X1"] - 8):
    for y in (-P["ZB_W"] / 2 + 8, P["ZB_W"] / 2 - 8): zb = zb.cut(cyl(3.4, 20, (x, y, zt), "Z")).cut(cyl(6.2, 7, (x, y, zt), "Z"))
zb = zb.cut(box(mx - 1, me - 0.5, sy - m / 2 - 1, sy + m / 2 + 1, zt - 1, zt + 1))           # 电机让位槽 1 mm
add("Z01_ZBase", zb, ALU)
r0 = zt + P["RISER_H"]
add("Z22_Riser", boxc(P["RAIL_X0"] - 4, P["RAIL_X1"] + 4, -8, 8, zt, r0, 0.8), BLK)
rt = r0 + P["RAIL_H"]
rail = box(P["RAIL_X0"], P["RAIL_X1"], -P["RAIL_W"] / 2, P["RAIL_W"] / 2, r0, rt)
rhx = [P["RAIL_X0"] + 5 + 15 * k for k in range(4)]
for x in rhx: rail = rail.cut(cyl(2.4, 12, (x, 0, rt), "Z")).cut(cyl(4.2, 2.4, (x, 0, rt), "Z"))
add("Z02_Rail", rail, STL)
add("Z02b_RailScrews", screws([(x, 0, rt - 0.62) for x in rhx], 3.6, 1.1), BLK)
xl = P["X_L1_INF"]; ct = rt + P["CAR_H"]; hw = P["CAR_W"] / 2
def ushape(x0, x1):
    return box(x0, x1, -hw, hw, rt - 3, ct).cut(box(x0 - 1, x1 + 1, -P["RAIL_W"] / 2 - 0.1, P["RAIL_W"] / 2 + 0.1, rt - 4, rt))
car = ushape(xl - 10.5, xl + 10.5)
for dx in (-4, 4):
    for dy in (-6, 6): car = car.cut(cyl(1.6, 6, (xl + dx, dy, ct), "Z"))
add("Z03_Carriage", car, STL)
add("Z03b_EndSeals", ushape(xl - 11.5, xl - 10.5).union(ushape(xl + 10.5, xl + 11.5)), (.12, .12, .13, 1))
# 墓碑形镜座：底板 + 立板（上部圆弧与光轴同心）
lh = boxc(xl - 8, xl + 8, -hw, hw, ct, ct + 2.5, 0.5).union(box(xl - 3, xl + 3, -11, 11, ct, A)).union(cyl(22, 6, (xl, 0, A)))
lh = lh.cut(box(xl - 12, xl + 12, -14, 14, 0, ct)).cut(cyl(11, 20, (xl, 0, A))).cut(cyl(P["L1_D"] + 0.2, 4.5, (xl + 0.75, 0, A)))   # 圆弧在滑块顶面以下的部分切掉
hp = [(xl + dx, dy) for dx in (-6, 6) for dy in (-5.5, 5.5)]
for (x, y) in hp: lh = lh.cut(cyl(2.2, 6, (x, y, ct + 1.25), "Z"))
add("Z04_LensHolder", lh, BLK)
add("Z04b_HolderScrews", screws([(x, y, ct + 3.2) for (x, y) in hp], 3.6, 1.4), BLK)
add("Z05_L1", cyl(P["L1_D"], 3, (xl, 0, A)), GLASS)
add("Z06_L1Ring", ring(12.8, 10, 1.5, (xl + 2.25, 0, A)), BLK)
# 浮动接头
add("Z07_CarriageTab", boxc(xl - 11.5, xl - 9, -14, -hw, sz - 5, ct, 0.3), BLK)
xn = xl - 2.5
nb = boxc(xn - 2.5, xn, sy - 10, -11, sz - 9, sz + 9, 0.4).cut(cyl(7, 10, (xn - 1.25, sy, sz)))
for dz in (-7.5, 7.5): nb = nb.cut(cyl(2.2, 10, (xn - 1.25, sy, sz + dz)))
add("Z07b_NutBracket", nb, BLK)
add("Z07c_BracketScrews", screws([(xn - 3.25, sy, sz + dz) for dz in (-7.5, 7.5)], 3.6, 1.5, "X"), BLK)
add("Z21_FloatBall", sphere(2, (xl - 7, -13, sz)), STL)
add("Z21b_PreloadSpring", coil(xl - 9, xl - 5, -12, sz - 3.5, 1.0, 0.2, 0.6), STL)
# 消隙螺母
nh = ring(20, 5.4, 3, (xn + 1.5, sy, sz)).union(ring(12, 10.2, 15, (xn + 10.5, sy, sz))).union(ring(12, 5.4, 0.5, (xn + 17.75, sy, sz)))
for dz in (-7.5, 7.5): nh = nh.cut(cyl(2.2, 4, (xn + 1.5, sy, sz + dz)))
add("Z08_NutHousing", nh, BRS)
add("Z08a_HalfNutA", ring(10, P["SCREW_D"], 5.5, (xn + 6.25, sy, sz)), (.95, .95, .92, 1))
add("Z08c_NutSpring", coil(xn + 9, xn + 12, sy, sz, 3.9, 0.3, 0.75), STL)
add("Z08b_HalfNutB", ring(10, P["SCREW_D"], 5.5, (xn + 14.75, sy, sz)), (.95, .95, .92, 1))
# 丝杠：固定端轴颈 Ø4（X59–74，台阶在 X74）| 螺纹 Ø5 | 支撑端轴颈 Ø4（螺纹用装饰线，不画槽）
x0s, t0, t1, x1s, J = P["SCREW_X0"], P["SCREW_TH0"], P["SCREW_TH1"], P["SCREW_X1"], P["SCREW_J"]
add("Z09_Screw", cyl(J, t0 - x0s, ((x0s + t0) / 2, sy, sz)).union(cyl(P["SCREW_D"], t1 - t0, ((t0 + t1) / 2, sy, sz))).union(cyl(J, x1s - t1, ((t1 + x1s) / 2, sy, sz))), STL)
def bearing(xc):                                                          # 带防尘盖的轴承外形（694ZZ）
    b = ring(P["BRG_OD"], P["BRG_OD"] - 1.6, P["BRG_W"], (xc, sy, sz)).union(ring(P["BRG_ID"] + 1.6, P["BRG_ID"], P["BRG_W"], (xc, sy, sz)))
    for s_ in (-1, 1): b = b.union(ring(P["BRG_OD"] - 1.6, P["BRG_ID"] + 1.6, 0.3, (xc + s_ * (P["BRG_W"] / 2 - 0.15), sy, sz)))
    return b
# 电机及固定端一体支座：电机板（止口）+ 轴承室（挡肩、锁紧螺母沉孔）+ 侧筋 + 底脚
f0, fL, mt = P["FB_X0"], P["FB_L"], P["MM_T"]; f1 = f0 + fL
db = boxc(me, me + mt, sy - 16, sy + 16, zt, sz + 16, 0.8).union(boxc(f0, f1, sy - 10, sy + 10, zt, sz + 10, 0.8))
db = db.union(box(me + mt - 0.5, f0 + 0.5, sy - 13, sy - 10, 22, sz + 7)).union(boxc(f0 - 9, f1, sy - 16, sy + 10, zt, zt + 4, 0.5))
db = db.cut(cyl(22.2, 10, (me + 2, sy, sz)))
mpts = [(sy + dy, sz + dz) for dy in (-11.5, 11.5) for dz in (-11.5, 11.5)]
for (y, z) in mpts: db = db.cut(cyl(2.7, 10, (me + 2, y, z)))
db = db.cut(cyl(10, 2 * (P["LOCKNUT_X0"] + 1.6 - f0), (f0, sy, sz)))                 # 锁紧螺母沉孔
db = db.cut(cyl(8.6, 30, (f0 + 1, sy, sz)))                                         # 挡肩孔（只碰外圈）
db = db.cut(cyl(P["BRG_OD"], 2 * (f1 - (f0 + 3)) + 0.02, (f1, sy, sz)))             # 轴承孔 X66–74
for (x, y) in ((f0 - 5, sy + 7), (f0 - 5, sy - 13.5)): db = db.cut(cyl(3.4, 20, (x, y, zt), "Z"))
for y in (sy - 14, sy + 14): db = db.cut(cyl(2.4, 16, (me + mt / 2, y, zt), "Z"))
add("Z14_DriveBracket", db, BLK)
add("Z10d_BearingPair", bearing(f0 + 5).union(bearing(f0 + 9)), STL)
lnx = P["LOCKNUT_X0"]
add("Z10b_LockNut", ring(8, J, 2, (lnx + 1, sy, sz)), BLK)
ct_ = P["CAP_T"]
cap = ring(18, 6.5, ct_, (f1 + ct_ / 2, sy, sz))
cpp = [(sy + 7 * math.cos(a * math.pi / 180), sz + 7 * math.sin(a * math.pi / 180)) for a in (90, 180, 270)]
for (y, z) in cpp: cap = cap.cut(cyl(2.2, 6, (f1 + ct_ / 2, y, z)))
add("Z10e_BearingCap", cap, BLK)
add("Z10f_CapScrews", screws([(f1 + ct_ + 0.6, y, z) for (y, z) in cpp], 3.4, 1.2, "X"), BLK)
# 支撑端：带底脚的轴承座（圆形轴承室 + 竖筋 + 底脚）
s0_, sL = P["SB_X0"], P["SB_L"]; sc = s0_ + sL / 2
sb = cyl(21, sL, (sc, sy, sz)).union(box(s0_, s0_ + sL, sy - 7, sy + 7, zt + 2, sz)).union(boxc(s0_ - 3, s0_ + sL + 3, sy - 14, sy + 10, zt, zt + 4, 0.5))
sb = sb.cut(cyl(P["BRG_OD"], 30, (sc, sy, sz)))
for x in (s0_ - 0.5, s0_ + sL + 0.5): sb = sb.cut(cyl(3.4, 20, (x, sy - 11, zt), "Z"))
add("Z11_BearingSup", sb, BLK)
add("Z11b_BearingSup", bearing(sc), STL)
# 联轴器
c0, cL, cd = P["CPL_X0"], P["CPL_L"], P["CPL_D"]
cp = ring(cd, 5, 3.5, (c0 + 1.75, sy, sz)).union(ring(cd, J, 3.5, (c0 + cL - 1.75, sy, sz))).union(ring(cd - 2.5, cd - 3.5, cL - 7, (c0 + cL / 2, sy, sz)))
for k in range(int(cL - 7)): cp = cp.union(ring(cd, cd - 3, 0.5, (c0 + 4 + k, sy, sz)))
for xc in (c0 + 1.75, c0 + cL - 1.75):
    cp = cp.cut(box(xc - 1.75, xc + 1.75, sy - 0.3, sy + 0.3, sz + 2, sz + 7)).cut(cyl(1.7, 14, (xc, sy, sz + 3.6), "Y"))
add("Z12_Coupling", cp, (.82, .84, .86, 1))
csx = None
for xc in (c0 + 1.75, c0 + cL - 1.75):
    t = cyl(1.6, 10, (xc, sy, sz + 3.6), "Y").union(cyl(2.8, 1.2, (xc, sy + 6.6, sz + 3.6), "Y")); csx = t if csx is None else csx.union(t)
add("Z12b_ClampScrews", csx, BLK)
# 电机 NEMA 11
mb = box(mx, me, sy - m / 2, sy + m / 2, sz - m / 2, sz + m / 2).edges("|X").chamfer(2.5)
for k in range(4): mb = mb.cut(ring(m + 2, m - 0.6, 0.6, (mx + 6 + k * 5, sy, sz)))
for (y, z) in mpts: mb = mb.cut(cyl(2.5, 8, (me, y, z)))
add("Z13_Motor", mb.union(cyl(22, 1.5, (me + 0.75, sy, sz))), (.12, .13, .15, 1))
add("Z13b_MotorShaft", cyl(5, c0 + 3.5 - me - 1.5, ((me + 1.5 + c0 + 3.5) / 2, sy, sz)).cut(box(me + 4, c0 + 4, sy - 3, sy + 3, sz + 2, sz + 3)), STL)
add("Z13c_MotorConn", box(mx + 3, mx + 13, sy - m / 2 - 4, sy - m / 2, sz - 4, sz + 4), (.92, .92, .90, 1))
add("Z14b_MountScrews", screws([(me + mt + 0.8, y, z) for (y, z) in mpts], 4.4, 1.6, "X"), BLK)
def slot_sensor(x):
    return box(x - 6, x + 6, 10, 22, zt, zt + 14).cut(box(x - 7, x + 7, 14.5, 17.5, zt + 4, zt + 15))
add("Z15_HomeSensor", slot_sensor(P["HOME_X"]), (.15, .15, .17, 1))
add("Z16_LimitSensor", slot_sensor(P["LIMIT_X"]), (.15, .15, .17, 1))
add("Z17_Flag", box(xl - 3, xl + 3, 15.5, 16.5, zt + 6, rt + 4).union(box(xl - 3, xl + 3, hw, 16.5, rt + 2, rt + 4)), (.85, .85, .2, 1))
sr, sf = P["STOP_REAR"], P["STOP_FRONT"]
add("Z23_HardStops", boxc(sr - 3, sr - 1, 4, 8, r0, rt + 4, 0.3).union(boxc(sf + 1, sf + 3, 4, 8, r0, rt + 4, 0.3)), BLK)
add("Z23b_Bumpers", box(sr - 1, sr, 4, 8, rt - 2, rt + 4).union(box(sf, sf + 1, 4, 8, rt - 2, rt + 4)), (.30, .30, .32, 1))
add("Z24_TransportLock", box(xl + 4, xl + 11, -13.5, -hw, zt, ct).union(cyl(3.6, 1.4, (xl + 7.5, -11, ct + 0.7), "Z")), (.90, .10, .10, 1))
sh = P["SHADE_D"]
add("Z18_ShadeTube", ring(sh, sh - 3, P["SHADE_X1"] - P["SHADE_X0"], ((P["SHADE_X0"] + P["SHADE_X1"]) / 2, 0, A)).union(ring(40, sh - 3, 4, (P["SHADE_X1"] - 2, 0, A))), BLK)
add("Z20_TempSensor", box(160, 168, 26, 31, zt, zt + 3), (.1, .5, .3, 1))

# ================= O 物镜组件（v0.8：墓碑形对中座 + 加强筋 + 底脚）=================
xm, s, T_ = P["XYM_X0"], P["XYM_S"], P["XYM_T"]; xo = P["X_OBJ"]
xym = box(xm, xm + T_, -s / 2, s / 2, zt, A).union(cyl(s, T_, (xm + T_ / 2, 0, A))).union(boxc(xm - 7, xm + T_, -s / 2, s / 2, zt, zt + 5, 0.5))
for y in (-s / 2 + 6, s / 2 - 6):
    xym = xym.union(cq.Workplane("XZ").polyline([(xm, zt + 5), (xm - 16, zt + 5), (xm, zt + 34)]).close().extrude(2.5, both=True).translate((0, y, 0)))
xym = xym.cut(box(xm - 30, xm + T_ + 1, -s, s, 0, zt)).cut(cyl(P["OBJ_TUBE_OD"] + 4, 20, (xm + T_ / 2, 0, A)))   # 圆弧在底座顶面以下的部分切掉
c = xm + T_ / 2; ro = P["OBJ_TUBE_OD"] / 2
for (dy, dz, ax) in ((0, 1, "Z"), (1, 0, "Y"), (-1, 0, "Y")):
    xym = xym.cut(cyl(4.2, s / 2 - ro + 4, (c, dy * (ro + s / 2) / 2, A + dz * (ro + s / 2) / 2), ax))
for y in (-s / 2 + 15, s / 2 - 15): xym = xym.cut(cyl(3.4, 20, (xm - 3.5, y, zt), "Z"))
add("O01_XYMount", xym, BLK)
add("O02_ObjTube", ring(P["OBJ_TUBE_OD"], P["OBJ_D"], 30, (xo, 0, A)).union(ring(P["OBJ_TUBE_OD"] + 8, P["OBJ_D"], 3, (xm + T_ + 1.5, 0, A))), BLK)
add("O03_Objective", cyl(P["OBJ_D"], 8, (xo, 0, A)), GLASS)
add("O04_ObjRing", ring(P["OBJ_D"] - 0.2, P["OBJ_D"] - 8, 3, (xo + 6, 0, A)), BLK)
cs = None
for (dy, dz, ax) in ((0, 1, "Z"), (1, 0, "Y"), (-1, 0, "Y")):
    L = s / 2 - ro + 2.5; rr = ro + 0.5 + L / 2
    t = cyl(4, L, (c, dy * rr, A + dz * rr), ax).union(cyl(7, 3, (c, dy * (s / 2 + 2.5), A + dz * (s / 2 + 2.5)), ax))
    cs = t if cs is None else cs.union(t)
add("O05_CenterScrews", cs, STL)

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
AUX = {"Z13c_MotorConn", "Z15_HomeSensor", "Z16_LimitSensor", "Z17_Flag", "Z20_TempSensor", "Z24_TransportLock"}   # 主体结构之外（以后按需加）
zm = cq.Assembly(name="调焦主体_v" + V.replace(".", "_"))
for pid, (shp, col) in SHP.items():
    if pid[0] == "Z" or pid.startswith("O0"): za.add(shp, name=pid, color=cq.Color(*col))
    if (pid[0] == "Z" or pid.startswith("O0")) and pid not in AUX: zm.add(shp, name=pid, color=cq.Color(*col))
zm.export(os.path.join(out, f"调焦主体_v{V}.step"))
zm.export(os.path.join(out, f"调焦主体_v{V}.glb"), "GLTF", tolerance=0.05, angularTolerance=0.3)
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
