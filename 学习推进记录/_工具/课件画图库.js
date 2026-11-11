const $=id=>document.getElementById(id);
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
const T=(x,y,t,s=14,c='var(--fg)',a='middle',w=400)=>`<text x="${x}" y="${y}" font-size="${s}" fill="${c}" text-anchor="${a}" font-weight="${w}">${t}</text>`;
function stepper(k,steps,state,draw){
  let i=0,anim=0;
  const dots=$('d'+k);dots.innerHTML=steps.map(()=>'<i></i>').join('');
  function go(n,instant){i=Math.max(0,Math.min(steps.length-1,n));const to={...state,...steps[i].s},from={...state},t0=performance.now(),dur=(reduce||instant)?0:700;
    cancelAnimationFrame(anim);
    const tick=now=>{const p=dur?Math.min(1,(now-t0)/dur):1,e=p<.5?2*p*p:1-(-2*p+2)**2/2;
      for(const key in to){if(typeof to[key]==='number')state[key]=from[key]+(to[key]-from[key])*e;else state[key]=to[key];}
      draw();if(p<1)anim=requestAnimationFrame(tick);};
    if(!dur){for(const key in to)state[key]=to[key];draw();}else anim=requestAnimationFrame(tick);
    $('c'+k).innerHTML=steps[i].t;$('n'+k).textContent=`第 ${i+1} / ${steps.length} 步`;
    dots.querySelectorAll('i').forEach((d,j)=>d.classList.toggle('on',j<=i));
    $('p'+k).disabled=i===0;$('x'+k).textContent=i===steps.length-1?'从头再看 ↺':'下一步 →';}
  $('p'+k).onclick=()=>go(i-1);$('x'+k).onclick=()=>go(i===steps.length-1?0:i+1);
  go(0,true);return {go,n:steps.length};
}
let TT=0;const ANIM=[];(function loop(){if(!reduce)TT+=0.016;ANIM.forEach(f=>f(TT));requestAnimationFrame(loop);})();
const DEFS=`<defs>
<linearGradient id="gCu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f7c89a"/><stop offset=".45" stop-color="#c9803f"/><stop offset="1" stop-color="#7a4216"/></linearGradient>
<linearGradient id="gCuS" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#a65f27"/><stop offset="1" stop-color="#6e3a12"/></linearGradient>
<linearGradient id="gAu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff2bf"/><stop offset=".5" stop-color="#e2b440"/><stop offset="1" stop-color="#9a7414"/></linearGradient>
<linearGradient id="gAuS" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#c79a26"/><stop offset="1" stop-color="#8a6610"/></linearGradient>
<linearGradient id="gSteel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f5f7fa"/><stop offset=".5" stop-color="#c2c9d2"/><stop offset="1" stop-color="#7b8592"/></linearGradient>
<linearGradient id="gSteelH" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8a94a1"/><stop offset=".35" stop-color="#eef1f5"/><stop offset=".7" stop-color="#b9c1cb"/><stop offset="1" stop-color="#6f7986"/></linearGradient>
<linearGradient id="gAlu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f0f3f6"/><stop offset="1" stop-color="#a9b2bc"/></linearGradient>
<linearGradient id="gPlate" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d9dee4"/><stop offset="1" stop-color="#aeb6c0"/></linearGradient>
<linearGradient id="gRod" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffc2c6"/><stop offset=".3" stop-color="#e8414f"/><stop offset=".75" stop-color="#a3121f"/><stop offset="1" stop-color="#5e0a12"/></linearGradient>
<linearGradient id="gGlass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#eaf6ff" stop-opacity=".95"/><stop offset=".25" stop-color="#bfe0f7" stop-opacity=".45"/><stop offset=".7" stop-color="#9cc7e6" stop-opacity=".35"/><stop offset="1" stop-color="#6fa3c9" stop-opacity=".7"/></linearGradient>
<linearGradient id="gLens" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#d7ecfb" stop-opacity=".9"/><stop offset=".5" stop-color="#f4fbff" stop-opacity=".6"/><stop offset="1" stop-color="#9cc7e6" stop-opacity=".9"/></linearGradient>
<linearGradient id="gJacket" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd08a"/><stop offset=".5" stop-color="#f08a1c"/><stop offset="1" stop-color="#a85508"/></linearGradient>
<linearGradient id="gYb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff59a"/><stop offset=".5" stop-color="#e3c22a"/><stop offset="1" stop-color="#9c8210"/></linearGradient>
<linearGradient id="gPlasma" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6c6ff"/><stop offset=".5" stop-color="#c25bd9"/><stop offset="1" stop-color="#7b2a92"/></linearGradient>
<linearGradient id="gLamp" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".5" stop-color="#fff7d1"/><stop offset="1" stop-color="#f3d27a"/></linearGradient>
<radialGradient id="gOn" cx=".35" cy=".32" r=".75"><stop offset="0" stop-color="#fff6dc"/><stop offset=".45" stop-color="#ffa346"/><stop offset="1" stop-color="#b8420a"/></radialGradient>
<radialGradient id="gOff" cx=".35" cy=".32" r=".75"><stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#b9c3cf"/><stop offset="1" stop-color="#5f6b7b"/></radialGradient>
<radialGradient id="gHalo"><stop offset="0" stop-color="#ffb347" stop-opacity=".7"/><stop offset="1" stop-color="#ffb347" stop-opacity="0"/></radialGradient>
<radialGradient id="gSpot"><stop offset="0" stop-color="#ffffff"/><stop offset=".3" stop-color="#ff5a5f"/><stop offset="1" stop-color="#ff2d2d" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="blur6" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
<filter id="shadow" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000" flood-opacity=".22"/></filter>
</defs>`;
function beam(x1,y1,x2,y2,w=6,a=1,col='#ff2d2d'){if(a<=0.01)return '';return `<g opacity="${a}"><line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${col}" stroke-width="${w*3.2}" opacity=".28" filter="url(#blur6)" stroke-linecap="round"/><line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${col}" stroke-width="${w}" opacity=".85" stroke-linecap="round"/><line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#fff3f3" stroke-width="${Math.max(1,w/3)}" stroke-linecap="round"/></g>`;}
function packet(x,y,ph=0,col='#ff4a2a',len=54,amp=7){let d='';for(let i=0;i<=len;i+=2){const e=Math.sin(Math.PI*i/len);d+=(i?'L':'M')+(x-len/2+i).toFixed(1)+','+(y-amp*e*Math.sin(i/len*5*Math.PI*2/2.2+ph)).toFixed(1);}return `<path d="${d}" fill="none" stroke="${col}" stroke-width="2.6" filter="url(#glow)" stroke-linecap="round"/>`;}
function tag(n,x,y,lx,ly,text,col){return `<line x1="${x}" y1="${y}" x2="${lx}" y2="${ly}" stroke="${col}" stroke-width="1.5"/><circle cx="${x}" cy="${y}" r="3.5" fill="${col}"/><circle cx="${lx}" cy="${ly}" r="11" fill="${col}"/>`+T(lx,ly+4.5,n,12,'#fff','middle',700)+(text?T(lx+(lx>x?16:-16),ly+5,text,12.5,'var(--fg)',lx>x?'start':'end',700):'');}
function quiz(QS){$('quiz').innerHTML=QS.map((q,i)=>`<div class="q" data-i="${i}"><p>Q${i+1}. ${q.q}</p><div class="row">${q.o.map((o,j)=>`<button data-j="${j}">${o}</button>`).join('')}</div><div class="fb" aria-live="polite"></div></div>`).join('');
document.querySelectorAll('.q button').forEach(b=>b.onclick=()=>{const qd=b.closest('.q'),q=QS[+qd.dataset.i],j=+b.dataset.j;
  qd.querySelectorAll('button').forEach(x=>x.classList.remove('right','wrong'));b.classList.add(j===q.a?'right':'wrong');
  qd.querySelector('.fb').textContent=(j===q.a?'✓ ':'✗ ')+q.e[j];});}
const C1='#e8590c',C2='#c2255c',C3='#1971c2';   // 三要素配色：① 泵浦 ② 发光材料 ③ 谐振腔
