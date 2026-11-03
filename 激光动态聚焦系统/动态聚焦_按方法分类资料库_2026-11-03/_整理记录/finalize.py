from collect import ROOT,CATS,safe
from pathlib import Path
import json,re,hashlib,html,urllib.parse,collections
import fitz
from bs4 import BeautifulSoup

meta=ROOT/'_整理记录'
sources=json.loads((meta/'sources.json').read_text(encoding='utf-8'))
records=[json.loads((meta/(s['id']+'.json')).read_text(encoding='utf-8')) for s in sources]
titles={
'R017':'Experimental investigation of 3D scanheads for laser micro-processing_2016_作者稿',
'R018':'Galvanometer driven optical system for laser dynamic focusing_2023',
'R019':'Galvanometer driven optical system for laser dynamic focusing_2023_ResearchGate',
'R021':'Optical design and analysis of a high-speed triple galvanometer laser 3D scanning system_2025',
'R022':'Doubled Z-axis scanning range and spot-quality enhancement_2026',
'R024':'Single-lens dynamic z-scanning_2023_TAG_全文镜像',
'R030':'SCANLAB_varioSCAN_II_eBox_官方规格书',
'R031':'Aerotech_AGV3D_产品页与安装使用手册',
'R032':'Aerotech_AGV3D_安装使用手册',
'R034':'RAYLASE_FOCUSSHIFTER_RD14_旧版失效链接',
'R036':'RAYLASE_AXIALSCAN_RD14_官方规格书_2026',
'R039':'Optotune_tunable_optics_for_laser_processing_2024',
'R041':'NIST_Methodologies and Implementation of Laser Powder-Bed Fusion Process Control_2023',
'R050':'艾思兰_CN116534252A_项目线索记录',
'R052':'江南大学项目清单_含艾思兰光束整形项目',
'R055':'Experimental investigation of 3D scanheads_ORCA机构库入口',
'R056':'激光大尺度3维动态聚焦扫描加工系统研究_2016',
'R057':'反射式扫描范围扩展_旧版失效入口',
'R058':'Model-driven 3D laser focus shifting_2025_出版社入口',
'R059':'Three-dimensional random-access confocal microscopy_2024',
'R061':'Aerotech激光加工产品总入口_返回异常内容',
'R066':'SCANLAB_varioSCAN_II旧PDF地址_已重定向至产品网页',
'R028':'Localized dynamic lensing via collinear light-sound interactions_2026',
}
bad=[]; seen={}; duplicates=[]; validation=[]
def remove_own(path):
 p=path.resolve()
 assert p.is_relative_to(ROOT.resolve()) and CATS[0] not in p.parts
 if p.exists(): p.unlink()

for r in records:
 rid=r['id']; r['title']=titles.get(rid,r.get('title') or r.get('context') or r['url'])
 r['title']=re.sub(r'\s+',' ',r['title']).strip()
 valid=[]
 for f in r['files']:
  p=ROOT/f['path']; data=p.read_bytes()
  if f['type']=='HTML':
   soup=BeautifulSoup(data,'html.parser'); title=soup.title.get_text(' ',strip=True) if soup.title else ''
   if data.startswith(b'\xff\xd8') or re.search(r'Captcha|Client Challenge|Checking your browser|Just a moment|Access Denied',title,re.I):
    bad.append({'id':rid,'path':f['path'],'reason':title or '非网页二进制内容'})
    remove_own(p); remove_own(p.with_suffix('.网页文本.txt'))
    r['attempts'].append({'url':f['url'],'error':'终检排除：'+(title or '非网页内容')}); continue
  if f['type']=='PDF':
   doc=fitz.open(p)
   for page in doc: page.get_text()
   doc[0].get_pixmap(matrix=fitz.Matrix(.3,.3)); doc[-1].get_pixmap(matrix=fitz.Matrix(.3,.3))
   f['pages']=len(doc); f['validation']='PDF签名、逐页解析、首末页渲染通过'; doc.close()
   validation.append({'id':rid,'path':f['path'],'pages':f['pages'],'result':f['validation']})
  sha=hashlib.sha256(data).hexdigest()
  if sha in seen:
   kept=seen[sha]
   if p!=ROOT/kept:
    remove_own(p)
    remove_own(p.with_suffix('.提取文本.txt' if f['type']=='PDF' else '.网页文本.txt'))
   f['path']=kept; f['duplicate']=True
   duplicates.append({'id':rid,'保留文件':kept,'SHA256':sha})
  else:
   if f['type']=='PDF':
    label=r['title'] if 'patents.google.com' in r['url'] or rid in titles or rid[0]!='R' else f.get('title') or r['title']
    if rid=='R023': label='TAG_2023_正文' if f['pages']==13 else 'TAG_2023_补充资料'
    if rid=='R025': label='全息10MHz_2024_正文' if f['pages']==10 else '全息10MHz_2024_公开审稿文件'
    new=p.parent/(rid+'_'+safe(label)+'.pdf')
    if new!=p and new.exists(): new=p.parent/(rid+'_'+safe(label)+'_'+sha[:6]+'.pdf')
    if new!=p:
     p.rename(new)
     txt=p.with_suffix('.提取文本.txt')
     if txt.exists(): txt.rename(new.with_suffix('.提取文本.txt'))
     p=new; f['path']=str(new.relative_to(ROOT))
   seen[sha]=f['path']
  f['sha256']=sha; valid.append(f)
 r['files']=valid
 r['status']='PDF已下载' if any(f['type']=='PDF' for f in valid) else ('补充材料已下载' if any(f['type'] in ['MOV','DOCX'] for f in valid) else ('网页已保存' if valid else '未获取'))
 if 'patents.google.com' in r['url'] and valid and not any(f['type']=='PDF' for f in valid): r['status']='专利全文网页已保存_无PDF附件'
 if rid in ['R016','R020','R026','B005']: r['status']='摘要或元数据网页已保存'
 if rid=='R027': r['status']='论文全文HTML已保存_未取得PDF'
 if rid=='B003': r['status']='在线手册入口已保存_非完整离线手册'
 if r.get('resolved_by'): r['status']='全文已由用户补齐 → '+r['resolved_by']
 r['origins']=sorted(set(r['origins']))
 (meta/(rid+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')

note='''本资料库按你提供的7个工作目录文件和1份粘贴文本整理，原件已全文读取并复制到00目录，工作目录原件未修改。
收集范围：原文明确引用的网页、论文、专利及资料文件；并补查原文提及的核心型号手册、有效替代入口、论文补充资料和一篇相关中文综述。
不是对互联网上全部动态聚焦文献的穷尽检索。仅写出品牌、没有具体型号或文献标题的泛称，不视为已定位到唯一资料。
资料分类依据光学执行方式；测高、同步和标定是共用控制层。可变发散角激光源单独列出，避免与移动透镜引起的发散角变化混淆。
PDF保留原始下载字节；提取文本用于搜索，公式、表格和图形请看原PDF。网页保存为HTML并附纯文本，但图片/CSS可能仍依赖联网。
“PDF已下载”包括论文、专利、厂商手册等，不能将总数当作论文数。作者稿、正文、补充材料、审稿文件分别标注。
未取得文件的来源保留在总索引和缺失清单，不以验证码页面、空网页或摘要充当全文。
原始AI调研中的价格、精度、专利有效性及设计建议保持原样备份，不因收录而被确认。
'''
missing='''重点缺口（2026-11-03）

1. Galvanometer driven optical system for laser dynamic focusing，10.1364/OE.476921：出版社PDF被验证码拦截，ResearchGate下载被拒绝；未取得本地论文全文。已有配套CN112068309B专利PDF。
2. Optical design and analysis of a high-speed triple galvanometer laser 3D scanning system，10.1016/j.optlastec.2024.111608：出版社及SSRN下载受限；未取得正式版或预印本全文。
3. Extending the 3D scanning range of reflective dynamic focusing device-based laser scanners，10.1364/OL.509656：已有出版社摘要网页，PDF下载被验证码拦截。
4. Doubled Z-axis scanning range and spot-quality enhancement...，10.1364/OE.588979：出版社及ResearchGate下载受限；未取得全文。
5. Processing curved surface with a high-speed triple galvanometer laser 3D scanning system，10.1364/OE.557541：已核实独立文献身份；出版社访问受限，未取得全文。
6. Model-driven 3D laser focus shifting...，10.1016/j.ijmachtools.2025.104310：已保存PolyU机构库记录，页面明确全文禁运至2027-08-31。
7. 激光大尺度3维动态聚焦扫描加工系统研究，10.7510/jgjs.issn.1001-3806.2016.04.002：已核对期刊入口；本机下载出现证书过期/连接失败，未取得PDF。
8. Localized dynamic lensing...，10.1007/s44258-025-00067-1：出版社本机请求返回Client Challenge，未取得全文。
9. MEMS Varifocal Optical Elements for Focus Control：PMC全文HTML已保存；PDF入口受验证或访问限制。
10. CN120928524B、CN121245003A、CN121742097A：已保存含说明书和权利要求的Google Patents全文网页，页面未提供PDF附件。

失效入口已有替代：FOCUSSHIFTER RD-14旧PDF→S009新版；2020快速调焦综述旧机构库地址→A001作者稿；共焦显微PMC受限入口→A003出版社全文；SCANLAB旧PDF→R030；ORCA扫描头论文入口→R017作者稿。

以下是未取得任何有效文件的具体请求记录（含同一资料的备用入口，不等于独立缺失文献数）：
'''
supplemented=[r for r in records if r.get('local_source')]
if supplemented:
 missing='重点缺口更新（2026-11-03）\n\n此前列出的8篇缺失论文现已全部由用户提供PDF补齐，并完成标题、DOI及文件有效性检查。\n\n已补齐：\n'+'\n'.join(r['id']+' '+r['title']+'\n'+r['files'][0]['path'] for r in supplemented)+'\n\n仍缺PDF版本（已有全文HTML）：MEMS Varifocal Optical Elements for Focus Control；CN120928524B、CN121245003A、CN121742097A。\n\n以下是其他失败入口的历史请求记录。部分已有同资料的有效替代入口；它们不代表核心论文仍然缺失。\n'
for r in records:
 if not r['files'] and not r.get('resolved_by'):
  missing+=f"\n{r['id']} {r['title']}\n{r['url']}\n"+'\n'.join(a.get('error','') for a in r['attempts'] if a.get('error'))+'\n'
(ROOT/'未获取全文与失效链接.txt').write_text(missing,encoding='utf-8-sig')

unique={f['path']:f for r in records for f in r['files']}
counts=collections.Counter(f['type'] for f in unique.values())
stats={'来源入口数':len(records),'取得有效文件的入口数':sum(bool(r['files']) for r in records),'唯一文件类型统计':dict(counts),'PDF总页数':sum(f.get('pages',0) for f in unique.values() if f['type']=='PDF'),'原始输入文件数':8,'已排除异常页面数':len(bad),'合并重复数':len(duplicates),'有效文件总字节':sum(f['bytes'] for f in unique.values())}
stats['用户补充PDF数']=len(supplemented)
(meta/'汇总统计.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
(meta/'文件验证记录.json').write_text(json.dumps({'统计':stats,'异常页面':bad,'重复文件':duplicates,'PDF校验':validation},ensure_ascii=False,indent=2),encoding='utf-8')
(meta/'完整下载清单.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'先读我.txt').write_text('激光动态聚焦：按方法分类资料库\n整理日期：2026-11-03\n\n'+note+'\n实际统计\n'+json.dumps(stats,ensure_ascii=False,indent=2)+'\n\n打开“资料总索引.html”，可按关键词和分类查找文件。\n未完成项查看“未获取全文与失效链接.txt”。\n',encoding='utf-8-sig')

def link(path,label): return '<a href="'+html.escape(urllib.parse.quote(str(path).replace('\\','/'),safe='/'))+'">'+html.escape(label)+'</a>'
rows=[]
for cat in CATS[1:]:
 entries=[r for r in records if r['category']==cat]
 txt=cat+'\n\n'
 for r in entries:
  txt+=f"{r['id']} | {r['title']}\n状态：{r['status']}\n来源：{r['url']}\n"+'\n'.join('文件：'+f['path'] for f in r['files'])+'\n\n'
  filelinks=[]
  linked_files=r['files']+next((x['files'] for x in records if x['id']==r.get('resolved_by')),[])
  for f in linked_files:
   label=f['type']+(f" · {f['pages']}页" if f.get('pages') else '')+(' · 同内容合并' if f.get('duplicate') else '')
   filelinks.append(link(f['path'],label))
   if f['type'] in ['PDF','HTML']:
    tp=Path(f['path']).with_suffix('.提取文本.txt' if f['type']=='PDF' else '.网页文本.txt')
    if (ROOT/tp).exists(): filelinks.append(link(tp,'可搜索文本'))
  rows.append('<tr data-cat="'+html.escape(cat)+'"><td>'+r['id']+'</td><td>'+html.escape(cat[3:])+'</td><td><strong>'+html.escape(r['title'])+'</strong><small>'+html.escape('；'.join(r['origins']))+'</small></td><td>'+html.escape(r['status'])+'</td><td>'+'<br>'.join(filelinks)+'</td><td><a href="'+html.escape(r['url'])+'">原始入口</a></td></tr>')
 (ROOT/cat/'本类目录.txt').write_text(txt or '暂无资料',encoding='utf-8-sig')
options=''.join('<option>'+html.escape(c)+'</option>' for c in CATS[1:])
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>激光动态聚焦资料库</title><style>body{font:15px/1.6 "Microsoft YaHei",sans-serif;margin:36px;color:#243143;background:#f4f6f8}h1{font-size:27px}p{max-width:1100px}input,select{padding:10px;margin:12px 8px 18px 0;min-width:280px}table{width:100%;border-collapse:collapse;background:white}th,td{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #dbe1e7}th{background:#203951;color:white;position:sticky;top:0}small{display:block;color:#76808c;margin-top:5px}a{color:#176eb7}strong{font-weight:500}</style><h1>激光动态聚焦 · 按方法分类资料库</h1>'''
page+=f"<p>2026-11-03 · 8份原始调研文件 · 用户补充{len(supplemented)}篇论文 · {counts['PDF']}份去重PDF · {counts['HTML']}份有效网页 · {counts['MOV']}个补充视频 · {counts['DOCX']}份补充文档</p>"
page+='<p>'+link('先读我.txt','使用说明')+'　'+link('未获取全文与失效链接.txt','缺失全文与失败原因')+'　'+link('_整理记录/原始文件清单.json','原始文件读取清单')+'</p><p>按资料中的方法归档。全文、摘要、产品页和手册入口已区分；总文件数不等于论文数。网页图片可能需要联网。搜索可输入专利号、厂商或论文标题。</p>'
page+='<input id="q" placeholder="搜索标题、编号、厂商"><select id="cat"><option value="">全部分类</option>'+options+'</select><table><thead><tr><th>编号</th><th>方法分类</th><th>资料</th><th>获取状态</th><th>本地文件</th><th>来源</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table><script>function filter(){let q=document.querySelector("#q").value.toLowerCase(),c=document.querySelector("#cat").value;document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!(r.textContent.toLowerCase().includes(q)&&(!c||r.dataset.cat===c)))}document.querySelector("#q").oninput=filter;document.querySelector("#cat").onchange=filter;</script></html>'
(ROOT/'资料总索引.html').write_text(page,encoding='utf-8')
print(json.dumps(stats,ensure_ascii=False,indent=2))
