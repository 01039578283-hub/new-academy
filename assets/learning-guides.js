/* Input stays in the current document; no network or persistent storage. */
(() => {
  const toc = document.querySelector('.lg-toc-panel');
  if (toc) {
    const mobile = window.matchMedia('(max-width: 780px)');
    const updateToc = () => { toc.open = !mobile.matches; };
    mobile.addEventListener('change', updateToc);
    updateToc();
  }
  const directory = document.querySelector('[data-guide-directory]');
  if (directory) {
    const search = directory.querySelector('[data-guide-search]');
    const audience = directory.querySelector('[data-guide-audience]');
    const category = directory.querySelector('[data-guide-category]');
    const cards = [...directory.querySelectorAll('[data-guide]')];
    const groups = [...directory.querySelectorAll('[data-guide-group]')];
    const normalize = value => value.normalize('NFKC').toLocaleLowerCase('ko-KR').replace(/\s+/g, '');
    const update = () => {
      const query = normalize(search.value);
      let count = 0;
      for (const card of cards) {
        const matches = (!query || normalize(card.dataset.search).includes(query)) &&
          (!audience.value || card.dataset.audience.split(' ').includes(audience.value)) &&
          (!category.value || card.dataset.category === category.value);
        card.hidden = !matches;
        if (matches) count++;
      }
      groups.forEach(group => { group.hidden = ![...group.querySelectorAll('[data-guide]')].some(card => !card.hidden); });
      directory.querySelector('[data-guide-status]').textContent = `${cards.length}개 중 ${count}개 가이드가 있습니다.`;
      directory.querySelector('[data-guide-empty]').hidden = count !== 0;
    };
    search.addEventListener('input', update);
    audience.addEventListener('change', update);
    category.addEventListener('change', update);
    directory.querySelector('[data-reset-filters]').addEventListener('click', () => {
      search.value = ''; audience.value = ''; category.value = ''; update(); search.focus();
    });
    directory.querySelector('[data-guide-filters]').hidden = false;
    update();
  }
  const form = document.querySelector('[data-record-form]');
  if (!form) return;
  form.hidden = false;
  form.addEventListener('submit', event => event.preventDefault());
  const fields = [...form.querySelectorAll('[data-record-field]')];
  const status = form.querySelector('[data-record-status]');
  const printable = document.querySelector('.lg-print-record');
  let printHandler;
  const makeRecord = () => {
    if (!fields.some(field => field.value.trim())) {
      status.textContent = '기록 항목을 한 가지 이상 작성해 주세요.';
      fields[0].focus();
      return null;
    }
    return `전문수업.com 학습 기록\r\n${form.dataset.title}\r\n작성 날짜: ${form.elements.date.value || '미입력'}\r\n\r\n` + fields.map(field => {
      const label = field.parentElement.childNodes[0].textContent.trim();
      return `${label}:\r\n${field.value.trim() || '(미작성)'}`;
    }).join('\r\n\r\n') + '\r\n';
  };
  form.querySelector('[data-save-record]').addEventListener('click', () => {
    const record = makeRecord();
    if (!record) return;
    const objectURL = URL.createObjectURL(new Blob(['\uFEFF', record], {type: 'text/plain;charset=utf-8'}));
    const link = document.createElement('a');
    link.href = objectURL;
    link.download = `${form.dataset.slug}-실천기록.txt`;
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(objectURL), 1500);
    status.textContent = '작성한 기록의 TXT 다운로드를 시작했습니다. 저장한 파일을 확인해 주세요.';
  });
  form.querySelector('[data-print-record]').addEventListener('click', () => {
    const record = makeRecord();
    if (!record) return;
    printable.textContent = record;
    document.body.classList.add('print-record');
    printHandler = () => { document.body.classList.remove('print-record'); };
    window.addEventListener('afterprint', printHandler, {once: true});
    window.print();
    document.body.classList.remove('print-record');
    window.removeEventListener('afterprint', printHandler);
    status.textContent = '인쇄 창에서 작성한 기록을 확인해 주세요.';
  });
})();
