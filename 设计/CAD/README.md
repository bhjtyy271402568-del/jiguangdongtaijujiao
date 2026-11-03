# CAD

| 文件 | 内容 |
|---|---|
| **调焦头_v0.2.step** | **当前**：详细结构装配体（55 种零件，带颜色，节点名 = BOM 编号）。SolidWorks / FreeCAD / Fusion 可打开 |
| focus_head_v0.2.glb | 同一模型的 glTF（网页 3D 用；课件里用的是转成 JSON 的版本） |
| BOM_v0.2.md | 零件清单（编号、名称、规格、自制 / 外购、参考来源） |
| 调焦头_v0.2_*_开盖.png | 渲染图（开盖、壳体半透明） |
| 调焦头_概念_v0.1.* | 旧的概念布局（已作废） |

全部由 `../工具/` 里的脚本生成，**不要手改**：

```
python 结构参数.py      # 改尺寸只改这里
python 生成CAD.py       # 需要 pip install cadquery
python 干涉检查.py      # 必须 0 处
python glb转json.py ../CAD/focus_head_v0.2.glb ../../学习推进记录/互动/focus_head_v0.2.json
```
