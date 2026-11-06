# -*- coding: utf-8 -*-
"""
Zemax 第 1 步：用“理想透镜”自动搭出调焦扩束镜（915 nm，1–10 m），并检查每个距离都能聚成一点。

怎么用（Windows，装好 OpticStudio）：
  1. 一次性：命令行运行  pip install pythonnet
  2. 打开 OpticStudio → 顶部 “Programming（编程）” 选项卡 → 点 “Interactive Extension（交互扩展）”，
     弹出等待连接的小窗口，别关。
  3. 命令行运行  python 第1步_理想透镜.py
  4. 回到 OpticStudio 看：Lens Data（镜头数据）、Multi-Configuration（多重结构）都已填好。
     脚本会把每一步“对应界面里哪个位置”打印出来，照着点一遍就学会了。

本脚本未在真实 OpticStudio 上跑过（编写环境没有 Zemax）；报错请把整段错误截图发回来。
数字来源：f1 −30 / f2 150 / 入射 4 mm 来自 设计/工具/结构参数.json（v0.8）；间距用薄透镜精确式【推算】。
"""
import os, sys

# ---------- 设计数据 ----------
LAM_UM = 0.915          # 波长 μm
EPD = 4.0               # 入瞳直径 mm（准直头出光）
F1, F2 = -30.0, 150.0   # 动镜、物镜焦距 mm
DIST_M = [1, 2, 3, 5, 10]   # 对焦距离 m（从物镜量起）

def spacing(L_m, f1=F1, f2=F2):
    """两镜间距 d：物镜把“动镜的虚焦点”成像到 L 处。"""
    L = L_m * 1000.0
    s = f2 * L / (L - f2)
    return s - abs(f1)

# ---------- 连接 OpticStudio ----------
def connect():
    try:
        import clr, winreg
    except ImportError:
        sys.exit("缺少 pythonnet：先运行  pip install pythonnet")
    key = winreg.OpenKey(winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER), r"Software\Zemax", 0, winreg.KEY_READ)
    root = winreg.QueryValueEx(key, "ZemaxRoot")[0]
    winreg.CloseKey(key)
    clr.AddReference(os.path.join(root, r"ZOS-API\Libraries\ZOSAPI_NetHelper.dll"))
    import ZOSAPI_NetHelper
    if not ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize():
        sys.exit("找不到 OpticStudio 安装目录")
    zdir = ZOSAPI_NetHelper.ZOSAPI_Initializer.GetZemaxDirectory()
    clr.AddReference(os.path.join(zdir, "ZOSAPI.dll"))
    clr.AddReference(os.path.join(zdir, "ZOSAPI_Interfaces.dll"))
    import ZOSAPI
    conn = ZOSAPI.ZOSAPI_Connection()
    app = conn.ConnectAsExtension(0)
    if app is None:
        sys.exit("连不上：先在 OpticStudio 里点 Programming → Interactive Extension，再运行本脚本")
    if not app.IsValidLicenseForAPI:
        sys.exit("当前许可证不支持 ZOS-API（Programming 选项卡里的功能用不了）")
    return ZOSAPI, app

def step(msg, where):
    print(f"● {msg}\n    界面里在：{where}")

def main():
    ZOSAPI, app = connect()
    S = app.PrimarySystem
    S.New(False)
    sd = S.SystemData

    # 系统设置
    ap = ZOSAPI.SystemData.ZemaxApertureType
    sd.Aperture.ApertureType = getattr(ap, "EntrancePuilDiameter", None) or getattr(ap, "EntrancePupilDiameter")  # ZOS-API 里这个枚举名本身拼错了
    sd.Aperture.ApertureValue = EPD
    step(f"孔径 = 入瞳直径 {EPD} mm", "左侧 System Explorer → Aperture")
    sd.Wavelengths.GetWavelength(1).Wavelength = LAM_UM
    step(f"波长 = {LAM_UM} μm", "System Explorer → Wavelengths")

    # 镜头数据：OBJ, STO, 动镜, 物镜, IMA
    LDE = S.LDE
    LDE.InsertNewSurfaceAt(2)
    LDE.InsertNewSurfaceAt(2)
    T = ZOSAPI.Editors.LDE.SurfaceType
    C = ZOSAPI.Editors.LDE.SurfaceColumn
    sto = LDE.GetSurfaceAt(1); sto.Thickness = 10.0; sto.Comment = "光阑（准直头出光口）"
    for idx, f, name in ((2, F1, "动镜 f1"), (3, F2, "物镜 f2")):
        s = LDE.GetSurfaceAt(idx)
        s.ChangeType(s.GetSurfaceTypeSettings(T.Paraxial))
        s.GetSurfaceCell(C.Par1).DoubleValue = f        # Paraxial 面的第 1 个参数 = 焦距
        s.Comment = name
    LDE.GetSurfaceAt(2).Thickness = spacing(DIST_M[0])
    LDE.GetSurfaceAt(3).Thickness = DIST_M[0] * 1000.0
    step("面 2 / 面 3 改成 Paraxial（理想薄透镜），焦距 −30 / 150",
         "Lens Data 表：Surface Type 列点开选 Paraxial，右边 Focal Length 填焦距")

    # 多重结构：每个距离一个配置，改面 2 厚度（间距 d）和面 3 厚度（距离 L）
    MCE = S.MCE
    for _ in DIST_M[1:]:
        MCE.AddConfiguration(False)
    MT = ZOSAPI.Editors.MCE.MultiConfigOperandType
    op_d = MCE.GetOperandAt(1); op_d.ChangeType(MT.THIC); op_d.Param1 = 2
    op_L = MCE.AddOperand();    op_L.ChangeType(MT.THIC); op_L.Param1 = 3
    for i, L in enumerate(DIST_M, start=1):
        op_d.GetOperandCell(i).DoubleValue = spacing(L)
        op_L.GetOperandCell(i).DoubleValue = L * 1000.0
    step(f"建 {len(DIST_M)} 个配置（{DIST_M} m），每个配置改 2 个厚度",
         "顶部 Setup → Editors → Multi-Configuration；THIC 2 = 两镜间距，THIC 3 = 对焦距离")

    # 检查：每个配置的 RMS 光斑半径（理想透镜下应 ≈ 0）
    MO = ZOSAPI.Editors.MFE.MeritOperandType
    print("\n配置 | 距离 | 两镜间距 d | 动镜后退量 | RMS 光斑半径（μm，应≈0）")
    for i, L in enumerate(DIST_M, start=1):
        MCE.SetCurrentConfiguration(i)
        rms = S.MFE.GetOperandValue(MO.RSCE, 3, 1, 0, 0, 0, 0, 0, 0) * 1000
        print(f"{i} | {L} m | {spacing(L):.2f} mm | {spacing(L) - (F2 + F1):.2f} mm | {rms:.3g}")
    MCE.SetCurrentConfiguration(1)
    step("想自己看：切换配置后打开点列图", "Multi-Configuration 表头点配置号（或按 Ctrl+A 轮换）；Analyze → Rays & Spots → Standard Spot Diagram")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "调焦扩束_915_理想透镜.zmx")
    S.SaveAs(out)
    print(f"\n已保存：{out}\n完成。把上面这张表和 OpticStudio 界面截图发给 Claude，再做第 2 步（换真实镜片）。")

if __name__ == "__main__":
    main()
