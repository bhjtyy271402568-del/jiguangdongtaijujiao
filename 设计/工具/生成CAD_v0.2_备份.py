"""
调焦头详细结构 v0.2：读 结构参数.json → STEP（装配体）、GLB（网页 3D）、视图 SVG、BOM
环境：pip install cadquery     运行：python 生成CAD.py
零件节点名 = BOM 编号（英文，便于各 CAD 软件识别）；中文名见 ../CAD/BOM_v0.2.md
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
assy = cq.Assembly(name="FocusHead_v0_2")
def add(pid, shape, color=None):
    g = pid[0]; assy.add(shape, name=pid, color=cq.Color(*(color or GC.get(g, (.6, .6, .6, 1)))))

# ================= H 壳体 =================
fl = P["FLOOR"]; lid = P["LID"]; px = P["PART_X"]; iy = HW / 2 - WA
base = box(0, HX, -HW / 2, HW / 2, 0, HH - lid).cut(box(WA, HX - WA, -iy, iy, fl, HH))
base = base.union(box(px, px + 6, -iy, iy, fl, HH - lid))                     # 隔断
base = base.cut(cyl(24, 30, (WA / 2, 0, A)))                                   # 入光孔
base = base.cut(cyl(34, 20, (px + 3, 0, A)))                                   # 隔断通光孔
base = base.cut(cyl(P["WIN_D"] - 4, 20, (P["GAL_X"], HW / 2 - WA / 2, OZ), "Y"))  # 侧面出光孔
base = base.cut(box(-1, WA + 1, 45 - 20, 45 + 20, 95 - 6, 95 + 6))            # DB25 开口
base = base.cut(cyl(16, 20, (WA / 2, 55, 30)))                                 # 电源插座孔
for x in (40, 180, 260, 330):                                                  # 上盖螺纹孔（示意）
    for y in (-iy + 3, iy - 3):
        base = base.cut(cyl(2.5, 14, (x, y, HH - lid - 6), "Z"))
add("H01_Base", base)
lidp = box(0, HX, -HW / 2, HW / 2, HH - lid, HH)
pts = [(x, y, HH - lid / 2) for x in (40, 180, 260, 330) for y in (-iy + 3, iy - 3)] + [(3, 0, HH - lid / 2), (HX - 3, 0, HH - lid / 2), (px + 3, -40, HH - lid / 2), (px + 3, 40, HH - lid / 2)]
for p in pts: lidp = lidp.cut(cyl(3.4, lid + 2, p, "Z"))
add("H02_Lid", lidp)
add("H03_LidScrews", screws([(p[0], p[1], HH + 1.5) for p in pts]), (.25, .25, .28, 1))
pads = None
for x in (25, HX - 25):
    for y in (-HW / 2 + 25, HW / 2 - 25):
        pd = box(x - 15, x + 15, y - 15, y + 15, -6, 0).cut(cyl(6.6, 8, (x, y, -3), "Z"))
        pads = pd if pads is None else pads.union(pd)
add("H04_MountPads", pads)

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
cbx = P["COMB_X"]
add("I07_Combiner", cyl(P["COMB_D"], 3, (0, 0, 0)).rotate((0, 0, 0), (0, 0, 1), -45).translate((cbx, 0, A)), GLASS)   # 法线 (0.707,-0.707)：红光 +Y 入射 → 反射向 +X
cm = ring(36, 24, 6, (0, 0, 0)).rotate((0, 0, 0), (0, 0, 1), -45).translate((cbx - 3.9, 3.9, A))
cm = cm.union(box(cbx - 9, cbx + 1, -2, 12, fl, A - 17))
add("I08_CombMount", cm, (.25, .27, .30, 1))
add("I09_RedModule", cyl(P["RED_D"], P["RED_L"], (cbx, P["RED_Y"], A), "Y"), (.95, .40, .40, 1))
add("I10_RedHolder", box(cbx - 9, cbx + 9, P["RED_Y"] - 7, P["RED_Y"] + 7, fl, A - P["RED_D"] / 2).union(ring(18, P["RED_D"], 10, (cbx, P["RED_Y"], A), "Y")))

# ================= Z 调焦机构 =================
zt = fl + P["ZB_T"]; zb = box(P["ZB_X0"], P["ZB_X1"], -P["ZB_W"] / 2, P["ZB_W"] / 2, fl, zt)
for x in (P["ZB_X0"] + 8, P["ZB_X1"] - 8):
    for y in (-P["ZB_W"] / 2 + 8, P["ZB_W"] / 2 - 8): zb = zb.cut(cyl(3.4, 20, (x, y, zt), "Z"))
add("Z01_ZBase", zb)
rt = zt + P["RAIL_H"]
add("Z02_Rail", box(P["RAIL_X0"], P["RAIL_X1"], -P["RAIL_W"] / 2, P["RAIL_W"] / 2, zt, rt), (.55, .57, .60, 1))
xl = P["X_L1_INF"]; ct = rt + P["CAR_H"]
add("Z03_Carriage", box(xl - P["CAR_L"] / 2, xl + P["CAR_L"] / 2, -P["CAR_W"] / 2, P["CAR_W"] / 2, rt, ct), (.45, .47, .50, 1))
lh = box(xl - 4, xl + 4, -14, 14, ct, A + 14).cut(cyl(11, 12, (xl, 0, A))).cut(cyl(P["L1_D"] + .3, 3.2, (xl + 2.5, 0, A)))
add("Z04_LensHolder", lh)
add("Z05_L1", cyl(P["L1_D"], 3, (xl + 2.5, 0, A)), GLASS)
add("Z06_L1Ring", ring(16, 10, 2, (xl + 5, 0, A)), (.25, .25, .28, 1))
sy, sz = P["SCREW_Y"], P["SCREW_Z"]
add("Z07_NutArm", box(xl - 5, xl + 5, sy + 7, -P["CAR_W"] / 2, rt + 1, ct - 0.5))
add("Z08_Nut", ring(14, P["SCREW_D"], 16, (xl, sy, sz)), (.80, .70, .30, 1))
add("Z09_Screw", cyl(P["SCREW_D"], P["SCREW_X1"] + 10 - P["SCREW_X0"] + 4, ((P["SCREW_X0"] - 4 + P["SCREW_X1"] + 10) / 2, sy, sz)), (.75, .75, .78, 1))
add("Z11_BearingSup", box(P["SCREW_X0"] - 6, P["SCREW_X0"] + 2, sy - 9, sy + 9, zt, sz + 9).cut(cyl(P["SCREW_D"] + 1, 20, (P["SCREW_X0"] - 2, sy, sz))))
add("Z10_BearingFix", box(P["SCREW_X1"], P["SCREW_X1"] + 10, sy - 10, sy + 10, zt, sz + 10).cut(cyl(P["SCREW_D"] + 1, 20, (P["SCREW_X1"] + 5, sy, sz))))
add("Z12_Coupling", cyl(14, 14, (P["SCREW_X1"] + 17, sy, sz)), (.80, .80, .82, 1))
mx = P["MOTOR_X0"]; m = P["MOTOR"]
add("Z13_Motor", box(mx, mx + P["MOTOR_L"], sy - m / 2, sy + m / 2, sz - m / 2, sz + m / 2).union(cyl(22, 2, (mx - 1, sy, sz))), (.18, .20, .24, 1))
add("Z14_MotorMount", box(mx - 4, mx, sy - m / 2 - 1, sy + m / 2 + 1, zt, sz + m / 2 + 1).cut(cyl(23, 10, (mx - 2, sy, sz))).union(box(mx - 16, mx - 4, sy - m / 2 - 1, sy + m / 2 + 1, zt, zt + 3)))
def slot_sensor(x):
    s = box(x - 6, x + 6, 10, 22, zt, zt + 14).cut(box(x - 7, x + 7, 14.5, 17.5, zt + 4, zt + 15))
    return s
add("Z15_HomeSensor", slot_sensor(P["HOME_X"]), (.15, .15, .17, 1))
add("Z16_LimitSensor", slot_sensor(P["LIMIT_X"]), (.15, .15, .17, 1))
add("Z17_Flag", box(xl - 3, xl + 3, 15.5, 16.5, zt + 6, rt + 3).union(box(xl - 3, xl + 3, P["CAR_W"] / 2, 16.5, rt + 2, rt + 4)), (.85, .85, .2, 1))
sh = P["SHADE_D"]
add("Z18_ShadeTube", ring(sh, sh - 3, P["SHADE_X1"] - P["SHADE_X0"], ((P["SHADE_X0"] + P["SHADE_X1"]) / 2, 0, A)), (.85, .87, .90, .45))
sad = None
for x in (P["RAIL_X1"] + 30, P["SHADE_X1"] - 14):
    s = box(x - 5, x + 5, -sh / 2 - 1.5, sh / 2 + 1.5, zt, A).cut(cyl(sh, 12, (x, 0, A)))
    sad = s if sad is None else sad.union(s)
add("Z19_ShadeSaddle", sad)
add("Z20_TempSensor", box(200, 208, 26, 31, zt, zt + 3), (.1, .5, .3, 1))

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
    b = box(304, 352, y0, y1, fl + 6, fl + 7.6).union(box(318, 342, (y0 + y1) / 2 - 10, (y0 + y1) / 2 + 10, fl + 7.6, fl + 20))
    for x in (308, 348):
        for y in (y0 + 4, y1 - 4): b = b.union(cyl(5, 6, (x, y, fl + 3), "Z"))
    return b
add("G08_DriverX", driver(-75, -10), (.10, .45, .25, 1))
add("G09_DriverY", driver(10, 75), (.10, .45, .25, 1))

# ================= W 保护窗 =================
wy = HW / 2
wf = ring(P["WIN_FR_OD"], P["WIN_D"] - 8, 8, (gx, wy + 4, OZ), "Y").cut(cyl(P["WIN_D"] + 0.4, 8.8, (gx, wy, OZ), "Y")).cut(ring(66.4, 61.6, 3.2, (gx, wy, OZ), "Y"))
add("W01_WinFrame", wf.union(screws([(gx + 32 * math.cos(a), wy + 9.5, OZ + 32 * math.sin(a)) for a in (0.785, 2.356, 3.927, 5.498)], 5.5, 3, "Y")), (.35, .37, .40, 1))
add("W02_Window", cyl(P["WIN_D"], P["WIN_T"], (gx, wy + 2, OZ), "Y"), GLASS)
add("W03_ORing", ring(66, 62, 1.5, (gx, wy + 0.75, OZ), "Y"), (.1, .1, .1, 1))

# ================= E 电子与接口 =================
sd = box(110, 170, iy - 4, iy - 2.4, fl + 8, fl + 58).union(box(130, 150, iy - 14, iy - 4, fl + 20, fl + 40))
for x in (114, 166):
    for z in (fl + 12, fl + 54): sd = sd.union(cyl(5, 2.4, (x, iy - 1.2, z), "Y"))
add("E01_StepDriver", sd, (.10, .45, .25, 1))
add("E02_DB25", box(-8, 0, 45 - 26.5, 45 + 26.5, 95 - 9, 95 + 9).union(box(-14, -8, 45 - 20, 45 + 20, 95 - 6, 95 + 6)), (.75, .75, .78, 1))
add("E03_PowerConn", cyl(20, 16, (-8, 55, 30)).union(cyl(26, 3, (-1.5, 55, 30))), (.30, .30, .32, 1))
add("E04_GroundStud", cyl(4, 12, (-6, 70, 18)), (.80, .65, .20, 1))

# ================= 参考光束（不属于零件）=================
xl5 = xl - D["travel"]
assy.add(cyl(4, xl - cx0 - cl, ((cx0 + cl + xl) / 2, 0, A)), name="R01_Beam", color=cq.Color(*GC["R"]))
assy.add(cq.Workplane().add(cq.Solid.makeCone(2, 10.5, xo - xl, cq.Vector(xl, 0, A), cq.Vector(1, 0, 0))), name="R02_BeamExpand", color=cq.Color(*GC["R"]))
assy.add(cyl(21, gx - xo, ((gx + xo) / 2, 0, A)), name="R03_Beam20", color=cq.Color(*GC["R"]))
assy.add(cyl(20, OZ - A, (gx, 0, (A + OZ) / 2), "Z"), name="R04_BeamUp", color=cq.Color(*GC["R"]))
assy.add(cyl(20, wy + 80, (gx, (wy + 80) / 2, OZ), "Y"), name="R05_BeamOut", color=cq.Color(*GC["R"]))

# ================= 输出 =================
out = os.path.join(here, "..", "CAD"); os.makedirs(out, exist_ok=True)
assy.export(os.path.join(out, "调焦头_v0.2.step"))
assy.export(os.path.join(out, "focus_head_v0.2.glb"), "GLTF", tolerance=0.08, angularTolerance=0.15)
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
md = ["# 调焦头 v0.2 零件清单（BOM）\n", "> 由 `工具/生成CAD.py` 生成。编号 = STEP / GLB 里的零件节点名。“做” = 自制件，“买” = 外购件。\n",
      "| 编号 | 子系统 | 名称 | 数量 | 规格 / 说明 | 做/买 | 参考 |\n|---|---|---|---|---|---|---|"]
for b in D["bom"]: md.append(f"| {b['id']} | {D['groups'][b['g']]} | {b['name']} | {b['qty']} | {b['spec']} | {b['make']} | {b['ref']} |")
mk = sum(1 for b in D["bom"] if b["make"] == "做"); md.append(f"\n共 {len(D['bom'])} 种：自制 {mk} 种，外购 {len(D['bom']) - mk} 种。")
open(os.path.join(out, "BOM_v0.2.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
bb = comp.BoundingBox()
print(f"完成：{len(D['bom'])} 种零件；包络 {bb.xlen:.0f} × {bb.ylen:.0f} × {bb.zlen:.0f} mm")
