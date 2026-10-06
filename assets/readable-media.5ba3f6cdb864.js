// Native links remain useful without JavaScript; large originals load on demand.
document.addEventListener('DOMContentLoaded',()=>{
 const links=[...document.querySelectorAll('a[data-readable-image]')];if(!links.length||typeof HTMLDialogElement==='undefined')return;
 const dialog=document.createElement('dialog');dialog.className='readable-media-dialog';dialog.setAttribute('aria-label','이미지 확대 보기');
 dialog.innerHTML='<div class="readable-media-tools"><button type="button" data-fit>화면에 맞추기</button><button type="button" data-actual>원본 크기</button><button type="button" data-plus aria-label="이미지 확대">＋</button><button type="button" data-minus aria-label="이미지 축소">－</button><a data-original target="_blank" rel="noopener">전체 원본</a><button type="button" data-close>닫기</button></div><p class="readable-media-title"></p><div class="readable-media-viewport" tabindex="0" aria-label="확대 이미지, 가로와 세로로 이동할 수 있습니다"><img alt=""></div><p class="readable-media-status" aria-live="polite"></p>';
 document.body.append(dialog);const image=dialog.querySelector('img'),viewport=dialog.querySelector('.readable-media-viewport'),status=dialog.querySelector('.readable-media-status');let owner=null,originalWidth=0,displayWidth=0;
 const resize=width=>{displayWidth=Math.max(180,Math.min(width,originalWidth*3));image.style.width=displayWidth+'px';status.textContent=`원본 가로 ${originalWidth}px · ${Math.round(displayWidth/originalWidth*100)}% 크기. 화면 안에서 가로·세로로 이동해 읽으세요.`;};
 const close=()=>dialog.close();
 links.forEach(link=>link.addEventListener('click',event=>{
  if(event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;event.preventDefault();owner=link;const source=link.querySelector('img');originalWidth=Number(link.dataset.originalWidth)||source.naturalWidth||Number(source.width)||918;
  image.alt=source.alt;dialog.querySelector('.readable-media-title').textContent=source.alt;dialog.querySelector('[data-original]').href=link.href;
  image.src=link.dataset.zoomSrc||link.href;dialog.showModal();document.body.classList.add('media-dialog-open');resize(originalWidth);viewport.scrollTop=0;viewport.scrollLeft=0;dialog.querySelector('[data-close]').focus();
 }));
 dialog.querySelector('[data-fit]').addEventListener('click',()=>resize(viewport.clientWidth));dialog.querySelector('[data-actual]').addEventListener('click',()=>resize(originalWidth));dialog.querySelector('[data-plus]').addEventListener('click',()=>resize(displayWidth*1.3));dialog.querySelector('[data-minus]').addEventListener('click',()=>resize(displayWidth/1.3));dialog.querySelector('[data-close]').addEventListener('click',close);
 dialog.addEventListener('click',e=>{if(e.target===dialog)close();});dialog.addEventListener('close',()=>{document.body.classList.remove('media-dialog-open');image.removeAttribute('src');owner?.focus();});
});
