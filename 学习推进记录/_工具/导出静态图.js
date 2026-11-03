// 从交互课件里导出静态 SVG（白底、浅色配色），供 GitHub 直接查看。
// 用法：node 导出静态图.js <课件.html> <输出目录>
// 课件中带 data-export="课号-序号_标题" 的 <svg> 会被导出；
// 若页面定义了 window.__beforeExport()，导出前先调用（例如把分步讲解跳到最后一步）。
// 若页面定义了 window.__frames[名字] = {count, names, show(i)}，则把每一帧拼成一张网格图。
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
(async()=>{
  const [html,out]=process.argv.slice(2);
  const b=await chromium.launch();
  const p=await b.newPage({viewport:{width:1000,height:900},colorScheme:'light',reducedMotion:'reduce'});
  await p.goto('file://'+path.resolve(html));await p.waitForTimeout(600);
  await p.evaluate(()=>window.__beforeExport&&window.__beforeExport());await p.waitForTimeout(200);
  const res=await p.evaluate(()=>{
    const cs=getComputedStyle(document.documentElement);
    const FONT='PingFang SC, Microsoft YaHei, Noto Sans CJK SC, WenQuanYi Zen Hei, sans-serif';
    const fix=s=>s.replace(/var\((--[\w-]+)\)/g,(m,v)=>cs.getPropertyValue(v).trim()||m);
    const ser=svg=>{const c=svg.cloneNode(true);
      c.querySelectorAll('[display="none"]').forEach(e=>e.remove());
      const vb=c.getAttribute('viewBox').split(/\s+/).map(Number);
      return {inner:fix(c.innerHTML),vb};};
    const wrap=(vb,inner)=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb.join(' ')}" font-family="${FONT}"><rect x="${vb[0]}" y="${vb[1]}" width="${vb[2]}" height="${vb[3]}" fill="#ffffff"/>${inner}</svg>`;
    const out=[];
    document.querySelectorAll('svg[data-export]').forEach(svg=>{
      const name=svg.dataset.export, fr=(window.__frames||{})[name];
      if(!fr){const {inner,vb}=ser(svg);out.push({name,svg:wrap(vb,inner)});return;}
      const cols=2,parts=[];for(let i=0;i<fr.count;i++){fr.show(i);parts.push(ser(svg));}
      const [w,h]=[parts[0].vb[2],parts[0].vb[3]+34],rows=Math.ceil(parts.length/cols);
      let s='';parts.forEach((pt,i)=>{const x=(i%cols)*w,y=Math.floor(i/cols)*h;
        s+=`<text x="${x+16}" y="${y+24}" font-size="18" font-weight="700" fill="#151a23">${i+1}. ${fr.names?fr.names[i]:''}</text>`;
        s+=`<svg x="${x}" y="${y+30}" width="${w}" height="${h-34}" viewBox="${pt.vb.join(' ')}">${pt.inner}</svg>`;});
      out.push({name,svg:wrap([0,0,w*cols,h*rows],s)});});
    return out;});
  fs.mkdirSync(out,{recursive:true});
  for(const r of res){fs.writeFileSync(path.join(out,r.name+'.svg'),r.svg);console.log('导出',r.name);}
  await b.close();
})();
