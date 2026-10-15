/* The existing map images stay visible. New maps load automatically near the viewport. */
(()=>{'use strict';
 const frames=[...document.querySelectorAll('iframe[data-kakao-src]')];
 const safePath=value=>{const u=new URL(value,location.href);return u.origin===location.origin&&/^\/assets\/kakao-maps\/\d+\/$/.test(u.pathname)?u.pathname+u.search:null;};
 function load(frame){
  const path=safePath(frame.dataset.kakaoSrc||'');if(!path||frame.dataset.kakaoLoaded===path)return;
  frame.dataset.kakaoLoaded=path;frame.src=path;
  const shell=frame.closest('.kd-map-shell');shell.removeAttribute('data-map-ready');shell.dataset.mapStarted='true';
  shell.querySelector('.kd-map-status').textContent='지도 위치를 자동으로 불러옵니다.';
  setTimeout(()=>{if(frame.dataset.kakaoLoaded===path&&!shell.hasAttribute('data-map-ready'))shell.querySelector('.kd-map-status').textContent='카카오맵 연결이 지연되고 있습니다. 아래 주소와 교통 안내를 확인해 주세요.';},12000);
 }
 window.addEventListener('message',event=>{
  if(event.origin!==location.origin||event.data?.type!=='wawa-kakao-ready')return;
  const f=frames.find(f=>f.contentWindow===event.source&&new URL(f.dataset.kakaoSrc,location.href).pathname==='/assets/kakao-maps/'+event.data.id+'/');
  if(f)f.closest('.kd-map-shell').dataset.mapReady='true';
 });
 if('IntersectionObserver' in window){
  const observer=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting){load(e.target);observer.unobserve(e.target);}},{rootMargin:'350px 0px'});
  frames.forEach(f=>observer.observe(f));
 }else frames.forEach(load);
 const safeLink=value=>{const u=new URL(value,location.href);return u.origin===location.origin?u.pathname+u.search+u.hash:null;};
 for(const select of document.querySelectorAll('[data-kakao-select]'))select.addEventListener('change',async()=>{
  const section=select.closest('.kakao-directions'),option=select.selectedOptions[0],frame=section.querySelector('iframe');
  const token=option.value;section.dataset.selection=token;frame.title=option.textContent+' 위치 지도';frame.dataset.kakaoSrc=token;load(frame);
  section.querySelector('.kd-address dd').textContent=option.dataset.address;
  const link=section.querySelector('.kd-hub-link'),target=safeLink(option.dataset.link);if(target){link.href=target;link.textContent=option.textContent+' 지점 안내';}
  const status=section.querySelector('.kd-hub-status');status.textContent=option.textContent+'의 위치를 표시합니다.';
  const traffic=section.querySelector('.kd-traffic-holder');traffic.replaceChildren();
  try{
   const url=new URL(option.dataset.traffic,location.href);if(url.origin!==location.origin||!/^\/assets\/kakao-traffic\/\d+\.json$/.test(url.pathname))return;
   const response=await fetch(url);if(!response.ok)throw Error('traffic');const data=await response.json();if(section.dataset.selection!==token)return;
   const list=document.createElement('ul');list.className='kd-traffic';
   for(const group of data){const li=document.createElement('li'),title=document.createElement('h3');title.textContent=group.title;li.append(title);const items=document.createElement(group.title==='주변 정류장'?'ol':'ul');items.className=group.className;
    group.items.forEach((value,index)=>{const item=document.createElement('li');if(group.className==='kd-stops'){const num=document.createElement('span');num.className='kd-stop-number';num.setAttribute('aria-hidden','true');num.textContent=String(index+1);item.append(num);}
     if(typeof value==='string'){const text=document.createElement('span');text.textContent=value;item.append(text);}else{const type=document.createElement('span');type.className='kd-bus-type kd-bus-'+value.type;type.textContent=value.label;const nums=document.createElement('span');nums.className='kd-bus-numbers';value.names.forEach(n=>{const text=document.createElement('span');text.textContent=n;nums.append(text);});item.append(type,nums);}items.append(item);});li.append(items);list.append(li);}
   traffic.append(list);
  }catch{if(section.dataset.selection===token)status.textContent+=' 주변 교통 정보는 지점 안내에서도 확인할 수 있습니다.';}
 });
})();
