from collect import *
extra=[
(8,'Variable optical elements for fast focus control_机构库作者稿','https://diposit.ub.edu/dspace/bitstream/2445/192696/1/704304.pdf'),
(2,'三振镜光学设计_SSRN预印本_2024','https://papers.ssrn.com/sol3/Delivery.cfm/23961627-8231-4cfa-adf1-3947f632d984-MECA.pdf?abstractid=4733403&mirid=1'),
(2,'振镜驱动动态聚焦_2023_出版社PDF入口','https://opg.optica.org/oe/viewmedia.cfm?seq=0&uri=oe-31-1-673'),
(1,'系统联合优化_2026_出版社PDF入口','https://opg.optica.org/oe/viewmedia.cfm?seq=0&uri=oe-34-8-14943'),
(2,'反射式扫描范围扩展_2023_出版社PDF入口','https://opg.optica.org/ol/viewmedia.cfm?uri=ol-48-24-6496&seq=0'),
(2,'三振镜曲面加工_2025_10.1364_OE.557541','https://opg.optica.org/oe/abstract.cfm?uri=oe-33-6-14314'),
(2,'三振镜曲面加工_2025_出版社PDF入口','https://opg.optica.org/oe/viewmedia.cfm?uri=oe-33-6-14314&seq=0'),
(7,'HALaser_E1803D控制卡完整手册','https://halaser.systems/manuals/e1803_manual.pdf'),
(1,'RAYLASE_FOCUSSHIFTER_RD14_有效新版2026','https://www.raylase.de/_Resources/Persistent/5/1/8/9/5189d9ad9239901c83aa37b1738071904ed74596/2026-03-16_Datenblatt_FOCUSSHIFTER%20RD-14_EN_v2.0.pdf'),
(1,'RAYLASE_AXIALSCAN30_Digital_II_HP','https://www.raylase.de/_Resources/Persistent/6/7/1/2/6712ab165f7dce513a0c934c651708e7256f153a/RAYLASE_AXIALSCAN-30%20DIGITAL%20II%20HP_en.pdf'),
(1,'Scanner_Optics_VCM_G1','https://ar.scanneroptics.com/products/scanner-optics-vcm-g1/'),
(1,'JCZ_G3_3D','https://en.bjjcz.cn/product/156.html'),
(5,'MEMS综述_出版社PDF','https://www.mdpi.com/2072-666X/16/4/482/pdf?version=1745050038'),
(5,'MEMS综述_出版社网页','https://www.mdpi.com/2072-666X/16/4/482'),
(10,'Renishaw_ATOM_DX数据表','https://www.renishaw.com/resourcecentre/download/data-sheet-atom-dx-miniature-encoder-system--142831?userLanguage=en'),
(10,'IKO_CRWG交叉滚柱导轨官方目录入口','https://ikowb01.ikont.co.jp/technicalservice/ikoc0130.php?FLG=CRWG&from=html&lang=en'),
(10,'THK_VR交叉滚柱导轨','https://www.thk.com/us/en/products/other_linear_motion_guides/cross_roller_guide_ball_guide/vr/'),
(10,'Akribis_AVM音圈电机规格','https://agito-akribis.com/wp-content/uploads/2022/02/AVM-Series-.pdf'),
(10,'Akribis音圈电机使用手册','https://www.akribis-sys.eu/uploads/files/website/Voice_coil_motor_user_manual.pdf'),
(1,'大尺度三维动态聚焦_中文期刊入口','https://www.jgjs.net.cn/cn/article/doi/10.7510/jgjs.issn.1001-3806.2016.04.002'),
]
items=json.loads((ROOT/'_整理记录'/'sources.json').read_text(encoding='utf-8'))
known={s['url'] for s in items}
for i,(cat,title,url) in enumerate(extra,1):
 if url not in known: items.append({'id':f'S{i:03}','url':url,'category':CATS[cat],'origins':['补充检索_原文提及条目及有效替代入口'],'context':title,'title':title})
(ROOT/'_整理记录'/'sources.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
todo=[s for s in items if not (ROOT/'_整理记录'/f"{s['id']}.json").exists()]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: list(pool.map(fetch,todo))
