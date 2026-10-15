/* Populate large optional map selectors shortly before they become visible. */
(()=>{'use strict';
 async function populate(select){
  if(select.dataset.optionsState==='loading'||select.dataset.optionsState==='ready')return;
  const url=new URL(select.dataset.kakaoHubOptions,location.href);
  if(url.origin!==location.origin||!/^\/assets\/kakao-hubs\/[a-f0-9]{16}\.json$/.test(url.pathname))return;
  select.dataset.optionsState='loading';
  try{
   const response=await fetch(url);if(!response.ok)throw Error('options');const rows=await response.json();
   const active=select.value,fragment=document.createDocumentFragment();
   for(const row of rows){
    const map=new URL(row.frame,location.href);if(map.origin!==location.origin||!/^\/assets\/kakao-maps\/\d+\/$/.test(map.pathname))continue;
    const option=document.createElement('option');option.value=row.frame;option.textContent=row.name;option.dataset.address=row.address;option.dataset.traffic=row.traffic;option.dataset.link=row.link;option.selected=row.frame===active;fragment.append(option);
   }
   if(fragment.childNodes.length){select.replaceChildren(fragment);select.dataset.optionsState='ready';}
   else throw Error('empty options');
  }catch{delete select.dataset.optionsState;}
 }
 const selects=[...document.querySelectorAll('[data-kakao-hub-options]')];
 if('IntersectionObserver' in window){
  const observer=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting){populate(e.target);observer.unobserve(e.target);}},{rootMargin:'600px 0px'});
  selects.forEach(s=>observer.observe(s));
 }else selects.forEach(populate);
 selects.forEach(s=>s.addEventListener('focus',()=>populate(s)));
})();
