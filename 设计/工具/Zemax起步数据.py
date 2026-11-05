"""给 Zemax 建模准备的起步数据：薄透镜下每个对焦距离对应的两镜间距。
运行：python3 Zemax起步数据.py → 写出 ../Zemax建模起步_v0.1.md 里的表（只替换表格部分）"""
import os, re
here = os.path.dirname(os.path.abspath(__file__))
DIST = [1, 2, 3, 5, 10, None]                      # m；None = 无穷远
def spacing(f2, f1, L):                            # 薄透镜：f2 把“f1 的虚焦点”成像到 L 处；L 从物镜量起
    s = f2 if L is None else f2 * L * 1000 / (L * 1000 - f2)
    return s - abs(f1), s - f2                     # 两镜间距、比无穷远多出的距离（= 动镜后退量）
rows = ["| 配置 | 对焦距离 L | 现方案 f2 150 / f1 −30：间距 d（后退量） | 短焦方案 f2 75 / f1 −15：间距 d（后退量） |", "|---|---|---|---|"]
for i, L in enumerate(DIST, 1):
    a = spacing(150, 30, L); b = spacing(75, 15, L)
    rows.append(f"| {i} | {'∞' if L is None else f'{L} m'} | {a[0]:.2f} mm（{a[1]:.2f}） | {b[0]:.2f} mm（{b[1]:.2f}） |")
table = "\n".join(rows)
p = os.path.join(here, "..", "Zemax建模起步_v0.1.md")
s = open(p, encoding="utf-8").read()
s = re.sub(r"<!-- 表开始 -->.*?<!-- 表结束 -->", "<!-- 表开始 -->\n" + table + "\n<!-- 表结束 -->", s, flags=re.S)
open(p, "w", encoding="utf-8").write(s)
print(table)
