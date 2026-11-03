"""
读 结构参数.json，用 CadQuery 生成调焦头概念装配体（STEP）和轴测线框图（SVG）。
环境：pip install cadquery
运行：python 生成CAD.py → ../CAD/调焦头_概念_v0.1.step、../CAD/调焦头_概念_v0.1_轴测.svg
说明：概念级模型，只表达布局、光轴、安装座和包络；零件选型后替换为真实模型。
"""
import json, os
import cadquery as cq
here = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(here, "结构参数.json"), encoding="utf-8"))
H = D["axis_h"]
P = {p["id"]: p for p in D["parts"]}

def cyl_x(d, L, x, y=0, z=H):      # 沿 X 的圆柱，中心在 (x,y,z)
    return cq.Workplane("YZ").circle(d / 2).extrude(L / 2, both=True).translate((x, y, z))
def ring_x(od, idd, L, x, y=0, z=H):
    return cq.Workplane("YZ").circle(od / 2).circle(idd / 2).extrude(L / 2, both=True).translate((x, y, z))
def box(L, W, Hh, x, y, z):         # 中心在 (x,y,z)
    return cq.Workplane("XY").box(L, W, Hh).translate((x, y, z))
def post(x, w, top, y=0):           # 从底板到 top 的支撑座
    return box(w, 24, top, x, y, top / 2)

assy = cq.Assembly(name="调焦头_概念_v0.1")
C = lambda r, g, b, a=1.0: cq.Color(r, g, b, a)
b = P["base"]; assy.add(box(b["L"], b["W"], b["H"], b["x"], 0, -b["H"] / 2), name="底板", color=C(.62, .66, .70))
# 激光准直器 + V 形夹持座
l = P["laser"]; assy.add(cyl_x(l["D"], l["L"], l["x"]), name="激光准直器", color=C(.90, .22, .23))
assy.add(post(l["x"] - 20, 16, H - l["D"] / 2) .union(post(l["x"] + 20, 16, H - l["D"] / 2)), name="准直器夹持座", color=C(.35, .38, .43))
# 合束镜（45°）+ 镜座 + 红光模组
c = P["comb"]
mir = cq.Workplane("YZ").circle(c["D"] / 2).extrude(1.5, both=True).rotate((0, 0, 0), (0, 0, 1), 45).translate((c["x"], 0, H))
assy.add(mir, name="合束镜", color=C(.49, .83, .99, .7))
assy.add(post(c["x"], 30, H - 16), name="合束镜座", color=C(.35, .38, .43))
r = P["red"]; assy.add(cq.Workplane("XZ").circle(r["D"] / 2).extrude(r["L"] / 2, both=True).translate((r["x"], r["y"], H)), name="红光模组", color=C(1, .42, .42))
assy.add(box(16, 16, H - 6, r["x"], r["y"], (H - 6) / 2), name="红光座", color=C(.35, .38, .43))
# 丝杠滑台 + 步进电机 + 动镜
s = P["stage"]; top = H - 20
assy.add(box(s["L"] + 20, s["W"], 12, s["x"], 0, 6), name="滑台底座", color=C(.42, .46, .53))
assy.add(box(s["L"] - 10, s["W"] - 4, 8, s["x"], 0, 16), name="滑台台面（动）", color=C(.55, .60, .68))
m = P["motor"]; assy.add(box(m["L"], m["W"], m["H"], m["x"], 0, 6 + m["H"] / 2), name="步进电机", color=C(.23, .26, .31))
assy.add(cq.Workplane("YZ").circle(3).extrude(35).translate((m["x"] + m["L"] / 2, 0, 6 + m["H"] / 2)), name="丝杠", color=C(.75, .75, .75))
assy.add(box(6, 8, 10, s["x"] - s["L"] / 2 - 8, 14, 11), name="原点开关", color=C(.09, .57, .31))
l1 = P["l1"]
assy.add(box(10, 20, top - 20, l1["x"], 0, 20 + (top - 20) / 2), name="动镜立柱（动）", color=C(.55, .60, .68))
assy.add(ring_x(l1["D"] + 10, l1["D"] - 1.5, 8, l1["x"]), name="动镜镜框（动）", color=C(.35, .38, .43))
assy.add(cyl_x(l1["D"], 3, l1["x"]), name="动镜 f-30", color=C(.31, .64, .88, .6))
# 遮光筒 + 物镜（带 XY 对中镜座）
t = P["tube"]; assy.add(ring_x(t["D"], t["D"] - 3, t["L"], t["x"]), name="遮光筒", color=C(.79, .81, .84, .5))
o = P["obj"]
assy.add(ring_x(o["D"] + 16, o["D"] - 2, 14, o["x"]), name="物镜镜框（XY对中）", color=C(.35, .38, .43))
assy.add(post(o["x"], 14, H - (o["D"] + 16) / 2), name="物镜座", color=C(.35, .38, .43))
assy.add(cyl_x(o["D"], 6, o["x"]), name="物镜 f150", color=C(.31, .64, .88, .6))
# 振镜头（包络）+ 转接板
g = P["galvo"]
gal = box(g["L"], g["W"], g["H"], g["x"], 0, H).faces("<X").workplane(centerOption="CenterOfBoundBox").hole(22, 15)
assy.add(gal, name="XY振镜头（包络）", color=C(.33, .38, .43))
assy.add(box(g["L"] + 10, g["W"] + 10, 6, g["x"], 0, 3), name="振镜转接板", color=C(.62, .66, .70))
# 保护窗
w = P["window"]
assy.add(ring_x(w["D"] + 12, w["D"] - 4, 10, w["x"]), name="保护窗框", color=C(.35, .38, .43))
assy.add(cyl_x(w["D"], 3, w["x"]), name="保护窗", color=C(.62, .85, 1, .4))
# 光束（参考体）
beam = cyl_x(4, D["x_l1_inf"] - 85, (85 + D["x_l1_inf"]) / 2)
cone = cq.Solid.makeCone(2, 10, D["x_obj"] - D["x_l1_inf"], cq.Vector(D["x_l1_inf"], 0, H), cq.Vector(1, 0, 0))
assy.add(beam, name="光束_4mm（参考）", color=C(1, .23, .23, .5))
assy.add(cq.Workplane().add(cone), name="光束_扩束段（参考）", color=C(1, .23, .23, .4))
assy.add(cyl_x(20, w["x"] - D["x_obj"], (w["x"] + D["x_obj"]) / 2), name="光束_20mm（参考）", color=C(1, .23, .23, .35))

out = os.path.join(here, "..", "CAD")
os.makedirs(out, exist_ok=True)
step = os.path.join(out, "调焦头_概念_v0.1.step")
assy.save(step)
comp = assy.toCompound()
cq.exporters.export(cq.Workplane().add(comp), os.path.join(out, "调焦头_概念_v0.1_轴测.svg"),
    opt={"width": 1000, "height": 520, "marginLeft": 20, "marginTop": 20, "projectionDir": (1.0, -1.6, 0.9),
         "showAxes": False, "strokeWidth": 0.4, "strokeColor": (40, 45, 55), "hiddenColor": (190, 195, 205), "showHidden": False})
# CadQuery 的 HLR 投影在这个视角下上下颠倒，翻转回来（只翻纵向）
import re
svgp = os.path.join(out, "调焦头_概念_v0.1_轴测.svg")
t = open(svgp, encoding="utf-8").read()
h = float(re.search(r'<svg[^>]*height="([0-9.]+)', t).group(1))
t = re.sub(r'(<svg[^>]*>)', r'\1<g transform="translate(0,%g) scale(1,-1)">' % h, t, count=1).replace("</svg>", "</g></svg>")
t = t.replace("<svg", '<svg style="background:#ffffff"', 1)
open(svgp, "w", encoding="utf-8").write(t)
bb = comp.BoundingBox()
print(f"已生成 {step}；包络 {bb.xlen:.0f} × {bb.ylen:.0f} × {bb.zlen:.0f} mm")
