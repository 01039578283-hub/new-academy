(() => {
  'use strict';
  const directory = document.querySelector('[data-ei-directory]');
  if (directory) {
    const cards = Array.from(directory.querySelectorAll('[data-ei-card]'));
    const search = directory.querySelector('[data-ei-search]');
    const category = directory.querySelector('[data-ei-category]');
    const audience = directory.querySelector('[data-ei-audience]');
    const format = directory.querySelector('[data-ei-format]');
    let page = 0;
    const pageSize = 12;
    const update = () => {
      const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
      const selected = cards.filter(card => (!category.value || card.dataset.category === category.value)
        && (!audience.value || card.dataset.audience.includes(audience.value)
          || (audience.value === '학생' && /초등|중등|고등/.test(card.dataset.audience)))
        && (!format.value || card.dataset.format === format.value)
        && terms.every(term => card.dataset.search.toLocaleLowerCase().includes(term)));
      const totalPages = Math.max(1, Math.ceil(selected.length / pageSize));
      page = Math.min(page, totalPages - 1);
      const visible = new Set(selected.slice(page * pageSize, (page + 1) * pageSize));
      cards.forEach(card => { card.hidden = !visible.has(card); });
      directory.querySelector('[data-ei-status]').textContent = `전체 ${cards.length}개 글 중 ${selected.length}개 · 현재 ${visible.size}개 표시`;
      directory.querySelector('[data-ei-empty]').hidden = selected.length > 0;
      directory.querySelector('[data-ei-page-status]').textContent = `${page + 1} / ${totalPages}`;
      directory.querySelector('[data-ei-prev]').disabled = page === 0;
      directory.querySelector('[data-ei-next]').disabled = page + 1 >= totalPages;
      directory.querySelector('[data-ei-pages]').hidden = selected.length === 0;
    };
    [search, category, audience, format].forEach(control => control.addEventListener(control === search ? 'input' : 'change', () => { page = 0; update(); }));
    directory.querySelector('[data-ei-reset]').addEventListener('click', () => { [search,category,audience,format].forEach(control => { control.value = ''; }); page = 0; update(); });
    directory.querySelector('[data-ei-prev]').addEventListener('click', () => { page--; update(); });
    directory.querySelector('[data-ei-next]').addEventListener('click', () => { page++; update(); });
    directory.querySelector('[data-ei-filters]').hidden = false;
    update();
  }
  const panel = document.querySelector('[data-ei-location]');
  if (!panel) return;
  const params = new URLSearchParams(location.search);
  const region = panel.querySelector('[data-location-region]');
  const center = panel.querySelector('[data-location-center]');
  const town = panel.querySelector('[data-location-town]');
  const centerLink = panel.querySelector('[data-center-link]');
  const townLink = panel.querySelector('[data-town-link]');
  const teacherLink = panel.querySelector('[data-profile-link]');
  fetch('/assets/education-info-locations.json').then(response => {
    if (!response.ok) throw new Error('Location list unavailable');
    return response.json();
  }).then(data => {
    const rows = data.centers;
    const options = (select, placeholder, values) => {
      select.replaceChildren(new Option(placeholder, ''), ...values.map(([label,value]) => new Option(label,value)));
    };
    options(region, '지역 선택', [...new Set(rows.map(row => row.region))].map(value => [value,value]));
    const retainContext = selected => {
      document.querySelectorAll('[data-ei-context-link]').forEach(link => {
        const url = new URL(link.href, location.origin);
        if (!url.pathname.startsWith('/%EA%B5%90%EC%9C%A1%EC%A0%95%EB%B3%B4/') && !decodeURIComponent(url.pathname).startsWith('/교육정보/')) return;
        url.search = '';
        if (selected) {
          url.searchParams.set('center', selected.name);
          if (town.value) url.searchParams.set('town', town.value);
        }
        link.href = url.pathname + url.search + url.hash;
      });
    };
    const updateLinks = () => {
      const selected = rows.find(row => row.name === center.value && row.region === region.value);
      const neighborhood = selected?.towns.find(row => row.name === town.value);
      centerLink.href = selected?.path || '/지점안내/';
      centerLink.textContent = selected ? `${selected.name} 위치·수업 안내` : '지점 위치·수업 안내';
      townLink.href = neighborhood?.path || (selected ? `/지점안내/${encodeURIComponent(selected.region)}/` : '/전국학원/');
      townLink.textContent = neighborhood ? `${neighborhood.name} 학원 안내` : '우리 동네 학원 안내';
      teacherLink.href = selected?.teacherPath || '/선생님찾기/';
      teacherLink.textContent = selected ? `${selected.name} 선생님 소개` : '선생님 소개 보기';
      panel.querySelector('[data-location-status]').textContent = selected ? `${selected.region} ${selected.district} · ${selected.name}${neighborhood ? ' · ' + neighborhood.name : ''} 안내로 연결됩니다.` : '지역과 지점을 선택하면 해당 안내로 연결됩니다.';
      retainContext(selected);
    };
    const updateTown = preferred => {
      const selected = rows.find(row => row.name === center.value && row.region === region.value);
      options(town, '동네 선택', (selected?.towns || []).map(row => [row.name,row.name]));
      town.disabled = !selected || selected.towns.length === 0;
      if (selected?.towns.some(row => row.name === preferred)) town.value = preferred;
      else if (selected?.towns.length === 1) town.value = selected.towns[0].name;
      updateLinks();
    };
    const updateCenter = () => {
      options(center, '지점 선택', rows.filter(row => row.region === region.value).map(row => [`${row.name} · ${row.district}`,row.name]));
      center.disabled = !region.value;
      updateTown('');
    };
    region.addEventListener('change', updateCenter);
    center.addEventListener('change', () => updateTown(''));
    town.addEventListener('change', updateLinks);
    const incoming = rows.find(row => row.name === params.get('center'));
    if (incoming) { region.value = incoming.region; updateCenter(); center.value = incoming.name; updateTown(params.get('town') || ''); }
    else updateLinks();
    panel.querySelector('[data-location-controls]').hidden = false;
  }).catch(() => {
    panel.querySelector('[data-location-status]').textContent = '아래 지점안내와 동네 안내에서 원하는 지역을 찾아보세요.';
  });
})();
