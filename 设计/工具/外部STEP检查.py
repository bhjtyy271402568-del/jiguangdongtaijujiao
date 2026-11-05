"""
检查别人（或 SolidWorks 等）导出的 STEP：零件清单对照、静态干涉、光路挡光、移动组件在行程两端的运动干涉。
用法：python 外部STEP检查.py <待查.step> [对照.step]
- 零件按名字里的 BOM 编号（如 Z03_Carriage）识别，前缀（如 V07_）会去掉
- 移动组件 = Z轴运动质量.json 里列的零件；光束、行程两端位置从 结构参数.json 来
"""
import sys, os, re, json, itertools
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.gp import gp_Trsf, gp_Vec, gp_Pnt, gp_Dir, gp_Ax2
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeCone
here = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(here, "结构参数.json"), encoding="utf-8"))["P"]
MOVK = set(json.load(open(os.path.join(here, "Z轴运动质量.json"), encoding="utf-8"))["moving_g"])
def load(path):
    doc = TDocStd_Document(TCollection_ExtendedString("d")); r = STEPCAFControl_Reader(); r.SetNameMode(True); r.ReadFile(path); r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); out = []
    def nm(l):
        a = TDataStd_Name(); return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), a) else "?"
    def walk(lab, loc):
        if st.IsAssembly_s(lab):
            seq = TDF_LabelSequence(); st.GetComponents_s(lab, seq)
            for i in range(1, seq.Length() + 1):
                c = seq.Value(i); ref = c; rl = TDF_Label()
                if st.IsReference_s(c): st.GetReferredShape_s(c, rl); ref = rl
                walk(ref, loc.Multiplied(st.GetLocation_s(c)))
        else:
            m = re.findall(r"([HIZOGWER]\d\d[a-z]?_[A-Za-z][A-Za-z0-9]*)", nm(lab))   # 取最后一个编号，去掉 V07_ 之类的前缀
            out.append((m[-1] if m else nm(lab), st.GetShape_s(lab).Moved(loc)))
    roots = TDF_LabelSequence(); st.GetFreeShapes(roots)
    for i in range(1, roots.Length() + 1): walk(roots.Value(i), TopLoc_Location())
    return out
def vol(s): p = GProp_GProps(); BRepGProp.VolumeProperties_s(s, p); return p.Mass()
def bbx(s): b = Bnd_Box(); BRepBndLib.Add_s(s, b); return b.Get()
def ovl(a, b):
    A, B = bbx(a), bbx(b)
    if A[3] < B[0] or B[3] < A[0] or A[4] < B[1] or B[4] < A[1] or A[5] < B[2] or B[5] < A[2]: return 0
    try: return vol(BRepAlgoAPI_Common(a, b).Shape())
    except Exception: return 0
def mv(s, dx): t = gp_Trsf(); t.SetTranslation(gp_Vec(dx, 0, 0)); return s.Moved(TopLoc_Location(t))
parts = load(sys.argv[1]); names = sorted({n for n, _ in parts})
print(f"# 外部 STEP 检查：{os.path.basename(sys.argv[1])}\n\n零件 {len(names)} 种（{len(parts)} 个实体）")
if len(sys.argv) > 2:
    ref = load(sys.argv[2]); rn = {n for n, _ in ref}
    def sig(L, n):
        ss = [s for k, s in L if k == n]; b = [bbx(s) for s in ss]
        return (round(min(x[0] for x in b), 1), round(min(x[1] for x in b), 1), round(min(x[2] for x in b), 1), round(max(x[3] for x in b), 1), round(max(x[4] for x in b), 1), round(max(x[5] for x in b), 1), round(sum(vol(s) for s in ss)))
    zo = lambda n: n[0] in "ZO"
    print("缺少（对照里有）：", sorted(n for n in rn - set(names) if zo(n)) or "无")
    print("新增（对照里没有）：", sorted(set(names) - rn) or "无")
    ch = [n for n in set(names) & rn if sig(parts, n) != sig(ref, n)]
    print("位置 / 体积有变化：", sorted(ch) or "无")
bad = [(v, a[0], b[0]) for a, b in itertools.combinations(parts, 2) if (v := ovl(a[1], b[1])) > 1]
print(f"\n静态干涉：{len(bad)} 处"); [print(f"- {v:.1f} mm³ {a} × {b}") for v, a, b in sorted(bad, reverse=True)]
A = P["AXIS_Z"]; xl = P["X_L1_INF"]; xo = P["X_OBJ"]
b1 = BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(P["APER_X"], 0, A), gp_Dir(1, 0, 0)), 2, xl - P["APER_X"]).Shape()
b2 = BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(xl, 0, A), gp_Dir(1, 0, 0)), 2, 10.5, xo - xl).Shape()
blk = [(v, bn, n) for bn, b in (("入射光束", b1), ("扩束光锥", b2)) for n, s in parts if n not in {"Z05_L1", "O03_Objective"} and (v := ovl(b, s)) > 0.5]
print(f"\n光路挡光：{len(blk)} 处"); [print(f"- {v:.1f} mm³ {b} × {n}") for v, b, n in blk]
MOV = [p for p in parts if p[0] in MOVK]; FIX = [p for p in parts if p[0] not in MOVK]
print(f"\n运动干涉（移动组件 {len(MOV)} 个实体整体沿光轴平移）：")
for x, lab in ((P["STOP_REAR"] + P["CAR_L"] / 2, "后硬限位"), (P["XL_5M"], "对焦 5 m"), (P["XL_50M"], "对焦 50 m"), (P["STOP_FRONT"] - P["CAR_L"] / 2, "前硬限位")):
    hits = [(v, m[0], f[0]) for m in MOV for f in FIX if not (f[0] == "Z09_Screw" and m[0].startswith("Z08")) and (v := ovl(mv(m[1], x - xl), f[1])) > 1]
    print(f"- 滑座中心 X = {x:.2f}（{lab}）：{len(hits)} 处" + "".join(f"；{v:.1f} mm³ {a} × {b}" for v, a, b in sorted(hits, reverse=True)[:5]))
