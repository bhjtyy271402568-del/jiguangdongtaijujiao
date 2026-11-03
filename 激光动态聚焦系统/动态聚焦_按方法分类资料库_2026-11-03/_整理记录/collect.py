from pathlib import Path
import re, json, hashlib, shutil, io, concurrent.futures, urllib.parse
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
CATS = ['00_原始调研材料','01_移动透镜式与匹配光学','02_反射式与三振镜调焦','03_液体与膜片可调透镜','04_TAG声学调焦','05_MEMS与全息调焦','06_可变发散角激光源','07_测高闭环_三轴同步与标定','08_综述与光学基础','09_艾思兰及相邻应用','10_执行器_导轨与编码器','99_待核实线索']
for cat in CATS: (ROOT/cat).mkdir(exist_ok=True)
HEADERS = {'User-Agent':'Mozilla/5.0 (compatible; ResearchDocumentCollection/1.0)'}
def safe(s): return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', s).strip(' .')[:105]
def classify(u, context=''):
    t=u.lower()
    groups=[(9,['cn111130015','cn111181117','cn210203085','cn116373177','cn116534252','cn110883020','patent9','jiangnan','oeshow','zhirongipp']), (2,['cn112068309','cn222506659','36607001','476921','366318787','509656','48-24-6496','s0030399224010661','4733403','40798223','triple_galvanometer']), (6,['us20240393604']), (7,['cn109894748','cn222626476','cn121742097','cn107315247','cn121245003','nist.gov','ezcad','halaser','935084']), (3,['optotune']), (4,['01303-2','single-lens-dynamic','00067-1']), (5,['47009-w','12029447','16/4/482']), (8,['0684-z','192696','gaussian-beam']), (1,['scanlab','raylase','aerotech','sino-galvo','feeltek','scanneroptics','haaslti','42071592','588979','3d_scanheads','3d-scanheads','114207','jgjs','115461','s0890695525000653','11555065'])]
    for c, keys in groups:
        if any(k in t for k in keys): return CATS[c]
    if 'patents.google.com/patent/' in t: return CATS[1]
    return CATS[11]

def build():
    inputs=[p for p in WORK.rglob('*') if p.is_file() and ROOT not in p.parents]
    attachment=Path(r'D:\codex\attachments\e07bae32-116d-4a77-9b2a-1f9a2e37df6d\已粘贴的文本.txt')
    inputs.append(attachment)
    sources={}; inventory=[]
    for p in inputs:
        raw=p.read_bytes(); body=raw.decode('utf-8-sig')
        rel=p.relative_to(WORK) if p.is_relative_to(WORK) else Path('用户粘贴_激光动态聚焦深度调研.txt')
        dest=ROOT/CATS[0]/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,dest)
        inventory.append({'原文件':str(p),'字节':len(raw),'字符':len(body),'SHA256':hashlib.sha256(raw).hexdigest(),'备份':str(dest.relative_to(ROOT)),'读取':'全文已读取'})
        for m in re.finditer(r'https?://[^\s<>\]\)"，；]+',body):
            url=m.group().rstrip('。.,;`*')
            if ',https' in url: continue
            url=url.split(',')[0]
            if url.startswith('https://patents.google.com/?'): continue
            url=url.replace('https://scanlab.de/','https://www.scanlab.de/')
            pm=re.search(r'patents.google.com/patent/([A-Z0-9]+)',url)
            if pm: url='https://patents.google.com/patent/'+pm[1]+('/zh' if pm[1].startswith('CN') else '/en')
            ctx=body[max(0,body.rfind('\n',0,m.start())):body.find('\n',m.end()) if '\n' in body[m.end():] else len(body)]
            if url not in sources: sources[url]={'url':url,'category':classify(url,ctx),'origins':[],'context':ctx[:1400]}
            sources[url]['origins'].append(str(rel))
        for patent in set(re.findall(r'\b(?:CN\d{9}[ABU]|US\d{8,11}[AB]\d)\b',body)):
            url='https://patents.google.com/patent/'+patent+('/zh' if patent.startswith('CN') else '/en')
            if url not in sources: sources[url]={'url':url,'category':classify(url),'origins':[str(rel)],'context':'原文提到的专利号，补全公开文本入口；标题及相关性待与原件核对'}
    for i,s in enumerate(sources.values(),1): s['id']=f'R{i:03}'
    (ROOT/'_整理记录'/'原始文件清单.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'_整理记录'/'sources.json').write_text(json.dumps(list(sources.values()),ensure_ascii=False,indent=2),encoding='utf-8')
    print('INPUTS',len(inputs),'SOURCES',len(sources),flush=True)

def fetch(s):
    folder=ROOT/s['category']; base=folder/s['id']; out=dict(s,files=[],attempts=[])
    seen=set()
    def get(u, suffix='', allow_html=True):
        if u in seen: return None
        seen.add(u)
        attempt={'url':u}; out['attempts'].append(attempt)
        try:
            r=requests.get(u,headers=HEADERS,timeout=(12,35)); attempt.update(http=r.status_code,final_url=r.url)
            r.raise_for_status(); data=r.content
            if data.lstrip().startswith(b'%PDF-'):
                reader=PdfReader(io.BytesIO(data)); n=len(reader.pages)
                if n<1: raise ValueError('PDF无页面')
                title=str((reader.metadata or {}).get('/Title','')).strip()
                path=folder/(s['id']+suffix+'_'+safe(title or urllib.parse.unquote(urllib.parse.urlparse(r.url).path.split('/')[-1]) or '全文')+'.pdf')
                path.write_bytes(data)
                text='\n\n'.join(p.extract_text() or '' for p in reader.pages)
                path.with_suffix('.提取文本.txt').write_text(text,encoding='utf-8')
                out['files'].append({'path':str(path.relative_to(ROOT)),'type':'PDF','pages':n,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'url':r.url,'text_chars':len(text),'title':title,'preview':text[:500]})
                attempt['result']='有效PDF'; return None
            if data.startswith(b'\xff\xd8') or b'<html' not in data[:6000].lower() and b'<!doctype html' not in data[:6000].lower():
                raise ValueError('返回内容不是PDF或HTML正文')
            soup=BeautifulSoup(data,'html.parser')
            title=soup.title.get_text(' ',strip=True) if soup.title else ''
            for x in soup(['script','style','noscript']): x.decompose()
            txt=soup.get_text('\n',strip=True)
            if re.search(r'^(Just a moment|Access Denied|Attention Required|Error|Redirecting|Client Challenge|Radware Captcha)',title,re.I) or 'Checking your browser' in txt[:500] or len(txt)<120:
                raise ValueError('验证/错误页面或正文过短: '+title)
            attempt['result']='网页'
            if allow_html:
                path=folder/(s['id']+suffix+'_'+safe(title or '来源网页')+'.html')
                path.write_bytes(data)
                path.with_suffix('.网页文本.txt').write_text('来源：'+r.url+'\n采集日期：2026-11-03\n\n'+txt,encoding='utf-8')
                out['files'].append({'path':str(path.relative_to(ROOT)),'type':'HTML','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'url':r.url,'title':title,'text_chars':len(txt)})
                out.setdefault('title',title)
            return soup,r.url
        except Exception as e: attempt['error']=str(e)[:400]; return None
    page=get(s['url'])
    if page:
        soup,url=page; links=[]
        for tag in soup.select('meta[name="citation_pdf_url"],meta[itemprop="pdfLink"]'):
            if tag.get('content'): links.append(urllib.parse.urljoin(url,tag['content']))
        for a in soup.select('a[href]'):
            h=urllib.parse.urljoin(url,a['href']); label=a.get_text(' ',strip=True)
            if '.pdf' in h.lower() and ('patent' in url or 'nature.com/articles/' in url or 'pmc.ncbi' in url or 'jgjs' in url or re.search(r'PDF|下载|Datasheet|Manual|规格|Download',label,re.I)):
                links.append(h)
        for i,u in enumerate(dict.fromkeys(links)):
            if i>=4: break
            get(u,f'_附件{i+1}',False)
    out['status']='PDF已下载' if any(x['type']=='PDF' for x in out['files']) else ('网页已保存_全文情况待核对' if out['files'] else '未获取')
    (ROOT/'_整理记录'/f"{s['id']}.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(s['id'],out['status'],s['url'],flush=True)
    return out

if __name__=='__main__':
    import sys
    if 'build' in sys.argv: build()
    else:
        items=json.loads((ROOT/'_整理记录'/'sources.json').read_text(encoding='utf-8'))
        todo=[s for s in items if not (ROOT/'_整理记录'/f"{s['id']}.json").exists()]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: list(pool.map(fetch,todo))
