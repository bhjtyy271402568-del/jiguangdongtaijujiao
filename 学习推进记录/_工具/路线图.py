"""生成课程路线图 SVG。改 STATIONS 和 DONE 后运行：python3 路线图.py"""
import os
STATIONS = [("①","光的旅程","全景"),("②","七种聚焦法","通用落在哪层"),("③","移动透镜光路","前/后聚焦"),("④","打得远的代价","前聚焦设计"),
            ("⑤","系统全貌","分层·流程·搭建顺序"),("⑥","50米换思路","光点·焦深·望远镜"),("⑦","需求落地","M²·档位·丝杠"),("⑧","结构与借鉴","3D·六个结构"),("⑨","镜片怎么动","丝杆·买还是做"),("⑩","Z轴传动设计","3D·16项校核"),("⑪","机构对比","六种·3D+2D·评分"),("⑫","看懂Zemax","光线·点列·波前"),("⑬","零件选型","真实型号·再校核")]
DONE = 12          # 已完成的课数
GOAL = "终点：《5–50 m 前聚焦系统规格》＝ 控制卡（项目①）+ 调焦望远镜（项目②，丝杠步进）+ 激光器（M²≤1.2）"
W = 940
ROWS = (len(STATIONS) + 3) // 4
H = 110 + ROWS * 130 + 10
F = "PingFang SC, Microsoft YaHei, Noto Sans CJK SC, WenQuanYi Zen Hei, sans-serif"
s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{F}">',
     f'<rect width="{W}" height="{H}" rx="16" fill="#ffffff"/>',
     '<text x="24" y="34" font-size="20" font-weight="700" fill="#111">课程路线图</text>',
     '<text x="150" y="34" font-size="13" fill="#666">先懂原理 → 定结构 → 搭样机验证 → 再做产品</text>']
pos = []
for i in range(len(STATIONS)):
    row = i // 4; col = i % 4 if row % 2 == 0 else 3 - i % 4
    pos.append((110 + col * 240, 110 + row * 130))
d = f"M{pos[0][0]},{pos[0][1]}"
for i in range(1, len(pos)):
    (x0, y0), (x1, y1) = pos[i - 1], pos[i]
    if y0 == y1:
        d += f" L{x1},{y1}"
    else:   # 换行：在右边（偶数行末）或左边（奇数行末）拐弯
        k = 90 if (i // 4) % 2 == 1 else -90
        d += f" C{x0+k},{y0} {x1+k},{y1} {x1},{y1}"
s.append(f'<path d="{d}" fill="none" stroke="#cbd5e1" stroke-width="6" stroke-linecap="round"/>')
for i, ((n, t, sub), (x, y)) in enumerate(zip(STATIONS, pos)):
    fill, st, tc = ("#16a34a", "#15803d", "#fff") if i < DONE else ("#fff7ed", "#ea580c", "#ea580c") if i == DONE else ("#fff", "#94a3b8", "#64748b")
    s.append(f'<circle cx="{x}" cy="{y}" r="22" fill="{fill}" stroke="{st}" stroke-width="3"/>')
    s.append(f'<text x="{x}" y="{y+6}" font-size="17" text-anchor="middle" fill="{tc}" font-weight="700">{"✓" if i < DONE else n}</text>')
    s.append(f'<text x="{x}" y="{y+48}" font-size="15" text-anchor="middle" fill="#111" font-weight="700">{t}</text>')
    s.append(f'<text x="{x}" y="{y+66}" font-size="12" text-anchor="middle" fill="#666">{sub}</text>')
if DONE < len(STATIONS):
    x, y = pos[DONE]
    s.append(f'<text x="{x}" y="{y-32}" font-size="12" text-anchor="middle" fill="#ea580c" font-weight="700">下一课 ▼</text>')
s.append(f'<rect x="20" y="{H-46}" width="{W-40}" height="28" rx="6" fill="#f1f5f9"/>')
s.append(f'<text x="{W//2}" y="{H-27}" font-size="13" text-anchor="middle" fill="#334155">{GOAL}</text>')
s.append('</svg>')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "图", "00_课程路线图.svg")
open(out, "w").write("\n".join(s))
print("已生成", os.path.normpath(out))
