/* Filter supplied profile information in the current page. */
(() => {
  const directory = document.querySelector('[data-teacher-directory]');
  if (!directory) return;
  const search = directory.querySelector('[data-teacher-search]');
  const region = directory.querySelector('[data-teacher-region]');
  const focus = directory.querySelector('[data-teacher-focus]');
  const cards = [...directory.querySelectorAll('[data-teacher-card]')];
  const status = directory.querySelector('[data-teacher-status]');
  const empty = directory.querySelector('[data-teacher-empty]');
  const pages = directory.querySelector('[data-teacher-pages]');
  const pageSize = pages ? 18 : cards.length;
  const normalize = value => value.normalize('NFKC').toLocaleLowerCase('ko-KR').replace(/\s+/g, '');
  let current = 0;
  let selected = cards;
  const render = () => {
    const pageCount = Math.ceil(selected.length / pageSize);
    current = Math.max(0, Math.min(current, Math.max(0, pageCount - 1)));
    const visible = new Set(selected.slice(current * pageSize, (current + 1) * pageSize));
    cards.forEach(card => { card.hidden = !visible.has(card); });
    empty.hidden = selected.length !== 0;
    const unit = directory.dataset.teacherDirectory === 'branches' ? '지점' : '소개';
    status.textContent = `${cards.length}개 ${unit} 중 ${selected.length}개가 있습니다.`;
    if (pages) {
      pages.hidden = pageCount <= 1;
      pages.querySelector('[data-page-status]').textContent = `${current + 1} / ${pageCount} 페이지`;
      pages.querySelector('[data-page-prev]').disabled = current === 0;
      pages.querySelector('[data-page-next]').disabled = current >= pageCount - 1;
    }
  };
  const filter = () => {
    const query = normalize(search.value);
    selected = cards.filter(card => (!query || normalize(card.dataset.search).includes(query)) &&
      (!region?.value || card.dataset.region === region.value) &&
      (!focus?.value || card.dataset.focus.includes(focus.value)));
    current = 0; render();
  };
  search.addEventListener('input', filter);
  region?.addEventListener('change', filter);
  focus?.addEventListener('change', filter);
  directory.querySelector('[data-teacher-reset]').addEventListener('click', () => {
    search.value = ''; if (region) region.value = ''; if (focus) focus.value = ''; filter(); search.focus();
  });
  if (pages) {
    pages.querySelector('[data-page-prev]').addEventListener('click', () => { current--; render(); directory.scrollIntoView({block:'start'}); });
    pages.querySelector('[data-page-next]').addEventListener('click', () => { current++; render(); directory.scrollIntoView({block:'start'}); });
  }
  const parameters = new URLSearchParams(location.search);
  if (region && [...region.options].some(option => option.value === parameters.get('region'))) region.value = parameters.get('region');
  if (parameters.get('q')) search.value = parameters.get('q').slice(0,150);
  directory.querySelector('[data-teacher-filters]').hidden = false;
  filter();
})();
