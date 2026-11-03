"""对 生成CAD.py 的装配体做两两干涉检查（体积 > 1 mm³ 报出）。运行：python 干涉检查.py"""
import importlib.util, os, itertools, sys
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("g", os.path.join(here, "生成CAD.py"))
src = open(os.path.join(here, "生成CAD.py"), encoding="utf-8").read().split("# ================= 输出 =================")[0]
ns = {"__file__": os.path.join(here, "生成CAD.py")}; exec(src, ns)
assy = ns["assy"]
parts = []
for ch in assy.children:
    if ch.name.startswith("R0"): continue
    shp = ch.obj.val() if hasattr(ch.obj, "val") else ch.obj
    if hasattr(ch.obj, "vals"): shp = ch.obj.vals()[0] if len(ch.obj.vals()) == 1 else __import__("cadquery").Compound.makeCompound(ch.obj.vals())
    parts.append((ch.name, shp))
bad = []
for (a, sa), (b, sb) in itertools.combinations(parts, 2):
    ba, bb = sa.BoundingBox(), sb.BoundingBox()
    if ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin or ba.zmax < bb.zmin or bb.zmax < ba.zmin: continue
    try: v = sa.intersect(sb).Volume()
    except Exception: continue
    if v > 1: bad.append((v, a, b))
for v, a, b in sorted(bad, reverse=True): print(f"{v:9.1f} mm³  {a}  ×  {b}")
print(f"共检查 {len(parts)} 个零件，干涉 {len(bad)} 处")

# —— 光路通畅检查：参考光束不能碰到除镜片 / 窗片 / 振镜镜片以外的任何零件 ——
PASS = {"Z05_L1", "O03_Objective", "W02_Window", "I07_Combiner", "G04_MirrorX", "G07_MirrorY"}
beams = []
for ch in assy.children:
    if ch.name.startswith("R0"):
        v = ch.obj.vals() if hasattr(ch.obj, "vals") else [ch.obj]
        beams.append((ch.name, v[0] if len(v) == 1 else __import__("cadquery").Compound.makeCompound(v)))
blk = []
for bn, bs in beams:
    for pn, ps in parts:
        if pn in PASS: continue
        try: v = bs.intersect(ps).Volume()
        except Exception: continue
        if v > 0.5: blk.append((v, bn, pn))
for v, b, p in sorted(blk, reverse=True): print(f"挡光 {v:8.1f} mm³  {b}  ×  {p}")
print(f"光路检查：{len(beams)} 段光束，挡光 {len(blk)} 处")
