from pathlib import Path
import json, hashlib, shutil, re
import pymupdf
from collect import ROOT, CATS

entries=[
('ol-48-24-6496.pdf',2,'2023_反射式动态聚焦_非球面校正与扫描范围扩展','10.1364/OL.509656',['R020','R057','S005']),
('oe-31-1-673.pdf',2,'2023_清华_振镜驱动反射式动态聚焦','10.1364/OE.476921',['R018','R019','S003','A004']),
('oe-34-8-14943.pdf',1,'2026_Z镜组_XY振镜_场镜系统联合优化','10.1364/OE.588979',['R022','S004','A005']),
('1-s2.0-S0030399224010661-main.pdf',2,'2025_高速三振镜三维扫描系统_光学设计与分析','10.1016/j.optlastec.2024.111608',['R021','S002']),
('oe-33-6-14314.pdf',2,'2025_高速三振镜三维扫描系统_曲面加工','10.1364/OE.557541',['S006','S007']),
('1-s2.0-S0890695525000653-main.pdf',1,'2025_模型驱动三维焦点移动_透明柔性聚合物微加工','10.1016/j.ijmachtools.2025.104310',['R026','R058']),
('s44258-025-00067-1.pdf',4,'2026_共线光声相互作用_局域动态调焦与扩展景深','10.1007/s44258-025-00067-1',['R028','A002']),
('激光大尺度3维动态聚焦扫描加工系统研究.pdf',1,'2016_激光大尺度3维动态聚焦扫描加工系统研究','10.7510/jgjs.issn.1001-3806.2016.04.002',['R056','S020','B004']),
]
meta=ROOT/'_整理记录'
sources=json.loads((meta/'sources.json').read_text(encoding='utf-8'))
log=[]
for i,(name,cat,title,doi,related) in enumerate(entries,1):
 src=Path('F:/发票')/name
 raw=src.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
 doc=pymupdf.open(src); text='\n\n'.join(page.get_text() for page in doc)
 assert doi.lower() in re.sub(r'\s+','',text).lower(), (name,'DOI mismatch')
 doc[0].get_pixmap(matrix=pymupdf.Matrix(.4,.4)); doc[-1].get_pixmap(matrix=pymupdf.Matrix(.4,.4))
 pages=len(doc); doc.close()
 rid=f'U{i:03}'; dst=ROOT/CATS[cat]/(rid+'_'+title+'.pdf')
 if dst.exists(): assert hashlib.sha256(dst.read_bytes()).hexdigest()==digest
 else: shutil.copy2(src,dst)
 dst.with_suffix('.提取文本.txt').write_text(text,encoding='utf-8')
 source=dict(id=rid,url='https://doi.org/'+doi,category=CATS[cat],title=title,context='用户提供的正式期刊全文PDF，已核对首页标题与DOI',origins=[str(src)],local_source=str(src),doi=doi)
 record=dict(source,status='PDF已下载',files=[dict(path=str(dst.relative_to(ROOT)),type='PDF',pages=pages,bytes=len(raw),sha256=digest,url='https://doi.org/'+doi,title=title,text_chars=len(text),validation='标题、DOI、逐页解析、首末页渲染通过')],attempts=[dict(source=str(src),result='用户提供本地PDF，复制归档，原件保留')])
 (meta/(rid+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
 if not any(s['id']==rid for s in sources): sources.append(source)
 for old in related:
  p=meta/(old+'.json'); r=json.loads(p.read_text(encoding='utf-8')); r['resolved_by']=rid
  r['resolution_note']='此前网络获取未完成；现已由用户提供正式版全文补齐。保留历史请求记录。'
  p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
 log.append(dict(id=rid,source=str(src),destination=str(dst),doi=doi,pages=pages,sha256=digest))
 assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
(meta/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
(meta/'用户补充PDF归档记录.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(log,ensure_ascii=False,indent=2))
