"""把 结构参数.json / Z轴传动计算.json 的数据填进课件里的 /*@SP*/…/*@end*/ 等标记（可重复运行）。用法：python 课件填数据.py 课件.html"""
import sys, json, os, re
here = os.path.dirname(os.path.abspath(__file__)); tools = os.path.join(here, "..", "..", "设计", "工具")
D = json.load(open(os.path.join(tools, "结构参数.json"), encoding="utf-8"))
C = json.load(open(os.path.join(tools, "Z轴传动计算.json"), encoding="utf-8"))
data = {"SP": {"P": D["P"], "f2": D["f2"], "version": D["version"]}, "BOM": D["bom"], "CALC": C}
f = sys.argv[1]; s = open(f, encoding="utf-8").read()
for k, v in data.items():
    s, n = re.subn(r"/\*@" + k + r"\*/.*?/\*@end\*/", lambda m: f"/*@{k}*/" + json.dumps(v, ensure_ascii=False, separators=(",", ":")) + "/*@end*/", s, flags=re.S)
    print(k, "填入" if n else "未找到标记")
open(f, "w", encoding="utf-8").write(s)
