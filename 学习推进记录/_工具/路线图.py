"""生成课程路线图 SVG。改 STATIONS 和 DONE 后运行：python3 路线图.py"""
import os
STATIONS = [("①","光的旅程","全景"),("②","七种聚焦法","通用落在哪层"),("③","移动透镜光路","前/后聚焦"),("④","打得远的代价","前聚焦设计"),
            ("⑤","系统全貌","分层·流程·搭建顺序"),("⑥","动镜模块","镜片·滑台·Z驱动"),("⑦","振镜与同步","XY2-100·Z提前"),("⑧","激光·安全·标定","开关光·防护·3D标定")]
DONE = 5          # 已完成的课数
GOAL = "终点：《前聚焦三轴系统规格》＝ 项目①控制卡 + 焦点接口 + 移动透镜 Z 模块（项目②）"
W, H = 940, 380
F = "PingFang SC, Microsoft YaHei, Noto Sans CJK SC, WenQuanYi Zen Hei, sans-serif"
s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{F}">',
     f'<rect width="{W}" height="{H}" rx="16" fill="#ffffff"/>',
     '<text x="24" y="34" font-size="20" font-weight="700" fill="#111">课程路线图</text>',
     '<text x="150" y="34" font-size="13" fill="#666">先懂原理（①–⑧）→ 再一起写系统规格 → 再动手设计</text>']
pos = []
for i in range(len(STATIONS)):
    row = i // 4; col = i % 4 if row == 0 else 3 - i % 4
    pos.append((110 + col * 240, 110 + row * 130))
s.append('<path d="M' + " L".join(f"{x},{y}" for x, y in pos[:4])
         + f" C{pos[3][0]+90},{pos[3][1]} {pos[4][0]+90},{pos[4][1]} {pos[4][0]},{pos[4][1]} L"
         + " L".join(f"{x},{y}" for x, y in pos[4:]) + '" fill="none" stroke="#cbd5e1" stroke-width="6" stroke-linecap="round"/>')
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
