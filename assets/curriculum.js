(() => {
  'use strict';
  const params = new URLSearchParams(location.search);
  const directory = document.querySelector('[data-cp-directory]');
  if (directory) {
    const cards = [...directory.querySelectorAll('[data-cp-card]')];
    const search = directory.querySelector('[data-cp-search]');
    const stage = directory.querySelector('[data-cp-stage]');
    const grade = directory.querySelector('[data-cp-grade]');
    const subject = directory.querySelector('[data-cp-subject]');
    let page = 0;
    const pageSize = 12;
    const gradeOptions = () => {
      const previous = grade.value;
      const grades = [...new Set(cards.filter(c => !stage.value || c.dataset.stage === stage.value).map(c => c.dataset.grade))];
      grade.replaceChildren(new Option('전체 학년', ''), ...grades.map(value => new Option(value, value)));
      if (grades.includes(previous)) grade.value = previous;
    };
    const update = () => {
      const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
      const filtered = cards.filter(c => (!stage.value || c.dataset.stage === stage.value)
        && (!grade.value || c.dataset.grade === grade.value)
        && (!subject.value || c.dataset.subject === subject.value)
        && terms.every(term => c.dataset.search.toLocaleLowerCase().includes(term)));
      const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
      page = Math.min(page, pages - 1);
      const visible = new Set(filtered.slice(page * pageSize, (page + 1) * pageSize));
      cards.forEach(c => { c.hidden = !visible.has(c); });
      directory.querySelector('[data-cp-status]').textContent = `전체 ${cards.length}개 계획 중 ${filtered.length}개 · 현재 ${visible.size}개 표시`;
      directory.querySelector('[data-cp-empty]').hidden = filtered.length > 0;
      directory.querySelector('[data-cp-page-status]').textContent = `${page + 1} / ${pages}`;
      directory.querySelector('[data-cp-prev]').disabled = page === 0;
      directory.querySelector('[data-cp-next]').disabled = page + 1 >= pages;
      directory.querySelector('[data-cp-pages]').hidden = filtered.length === 0;
    };
    stage.addEventListener('change', () => { page = 0; gradeOptions(); update(); });
    [search, grade, subject].forEach(el => el.addEventListener(el === search ? 'input' : 'change', () => { page = 0; update(); }));
    directory.querySelector('[data-cp-reset]').addEventListener('click', () => {
      search.value = ''; stage.value = ''; gradeOptions(); grade.value = ''; subject.value = ''; page = 0; update();
    });
    directory.querySelector('[data-cp-prev]').addEventListener('click', () => { page--; update(); });
    directory.querySelector('[data-cp-next]').addEventListener('click', () => { page++; update(); });
    for (const [control, key] of [[stage, 'stage'], [subject, 'subject']]) {
      if ([...control.options].some(o => o.value === params.get(key))) control.value = params.get(key);
    }
    gradeOptions();
    if ([...grade.options].some(o => o.value === params.get('grade'))) grade.value = params.get('grade');
    directory.querySelector('[data-cp-filters]').hidden = false;
    update();
  }
  const groups = document.querySelector('[data-cp-groups]');
  if (groups) {
    const stage = groups.querySelector('[data-group-stage]');
    const subject = groups.querySelector('[data-group-subject]');
    const rows = [...groups.querySelectorAll('[data-cp-group]')];
    const update = () => {
      rows.forEach(row => { row.hidden = (!!stage.value && row.dataset.stage !== stage.value) || (!!subject.value && row.dataset.subject !== subject.value); });
      const count = rows.filter(row => !row.hidden).length;
      groups.querySelector('[data-group-status]').textContent = `${count}개 학교급·과목 조합 · ${count * 3}개 수준별 학습 방법`;
    };
    stage.addEventListener('change', update); subject.addEventListener('change', update);
    groups.querySelector('[data-group-controls]').hidden = false; update();
  }
  const panel = document.querySelector('[data-cp-location]');
  if (!panel) return;
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
    const options = (select, placeholder, values) => select.replaceChildren(new Option(placeholder, ''), ...values.map(([label, value]) => new Option(label, value)));
    options(region, '지역 선택', [...new Set(rows.map(row => row.region))].map(value => [value, value]));
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
      document.querySelectorAll('[data-cp-context]').forEach(link => {
        const url = new URL(link.href, location.origin);
        if (!decodeURIComponent(url.pathname).startsWith('/학습커리큘럼/')) return;
        url.searchParams.delete('center'); url.searchParams.delete('town');
        if (selected) {
          url.searchParams.set('center', selected.name);
          if (neighborhood) url.searchParams.set('town', neighborhood.name);
        }
        link.href = url.pathname + url.search + url.hash;
      });
    };
    const updateTown = preferred => {
      const selected = rows.find(row => row.name === center.value && row.region === region.value);
      options(town, '동네 선택', (selected?.towns || []).map(row => [row.name, row.name]));
      town.disabled = !selected || selected.towns.length === 0;
      if (selected?.towns.some(row => row.name === preferred)) town.value = preferred;
      else if (selected?.towns.length === 1) town.value = selected.towns[0].name;
      updateLinks();
    };
    const updateCenter = () => {
      options(center, '지점 선택', rows.filter(row => row.region === region.value).map(row => [`${row.name} · ${row.district}`, row.name]));
      center.disabled = !region.value; updateTown('');
    };
    region.addEventListener('change', updateCenter);
    center.addEventListener('change', () => updateTown(''));
    town.addEventListener('change', updateLinks);
    const incoming = rows.find(row => row.name === params.get('center'));
    if (incoming) { region.value = incoming.region; updateCenter(); center.value = incoming.name; updateTown(params.get('town') || ''); }
    else updateLinks();
    panel.querySelector('[data-location-controls]').hidden = false;
  }).catch(() => { panel.querySelector('[data-location-status]').textContent = '아래 지점안내와 동네 안내에서 원하는 지역을 찾아보세요.'; });
})();
