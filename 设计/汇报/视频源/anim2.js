const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});const p=await b.newPage({viewport:{width:1920,height:1080}});
p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('http://127.0.0.1:8765/anim2.html');await p.waitForFunction(()=>window.ready,null,{timeout:180000});
const cam=JSON.parse(process.argv[2]);const out=process.argv[3];const FPS=25;const list=process.argv[4]?process.argv[4].split(',').map(Number):[...Array(Math.round(21.2*FPS)).keys()];
require('fs').mkdirSync(out,{recursive:true});
for(const i of list){await p.evaluate(([t,cam])=>setT(t,cam),[i/FPS,cam]);await p.screenshot({path:`${out}/f${String(i).padStart(4,'0')}.png`});}
await b.close();})();
