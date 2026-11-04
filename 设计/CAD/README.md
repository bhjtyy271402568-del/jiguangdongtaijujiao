# CAD

| 文件 | 内容 |
|---|---|
| **调焦头_v0.4.step** | **当前**：Z 轴传动链按机械设计重做（固定—支撑轴承、消隙螺母、球头浮动接头、波纹管联轴器、运输锁），77 种零件，干涉 0、挡光 0 |
| z_axis_v0.4.glb | 只含 Z 轴 + 物镜的子装配（第 11 课 3D 用） |
| BOM_v0.4.md | 当前零件清单 |
| 调焦头_v0.3.step | 上一版（59 种零件） |
| 调焦头_v0.3_*.png | 渲染图：外观、开盖、俯视、仰视、Z 机构近景、振镜腔近景、剖开 |
| BOM_v0.3.md | v0.3 零件清单 |
| 调焦头_v0.2.step | 上一版详细结构（55 种） |
| focus_head_v0.2.glb | 同一模型的 glTF（网页 3D 用；课件里用的是转成 JSON 的版本） |
| BOM_v0.2.md | 零件清单（编号、名称、规格、自制 / 外购、参考来源） |
| 调焦头_概念_v0.1.* | 旧的概念布局（已作废） |

全部由 `../工具/` 里的脚本生成，**不要手改**：

```
python 结构参数.py      # 改尺寸只改这里
python 生成CAD.py       # 需要 pip install cadquery
python 干涉检查.py      # 干涉、光路挡光都必须 0 处
python Z轴传动计算.py   # Z 轴设计校核（读 生成CAD.py 写出的 Z轴运动质量.json）
python glb转json.py ../CAD/focus_head_v0.3.glb ../../学习推进记录/互动/focus_head_v0.3.json
python glb转json.py ../CAD/z_axis_v0.4.glb ../../学习推进记录/互动/z_axis_v0.4.json
```
