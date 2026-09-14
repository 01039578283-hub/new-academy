/* Progressive enhancement: every directory link remains in the HTML without JS. */
(() => {
  'use strict';

  const initialize = () => {
    const root = document.querySelector('body.branch-directory');
    if (!root) return;

    const query = root.querySelector('[data-branch-query]');
    const cards = Array.from(root.querySelectorAll('[data-branch-card]'));
    if (!query || cards.length === 0) return;

    const form = query.closest('form');
    const region = root.querySelector('[data-branch-region]');
    const reset = root.querySelector('[data-branch-reset]');
    const status = root.querySelector('[data-branch-count]');
    const empty = root.querySelector('[data-branch-empty]');
    const groups = Array.from(root.querySelectorAll('[data-branch-group]'));
    let composing = false;

    // NFKC also matches full-width characters and composed Korean input.
    const normalize = (value) => String(value || '')
      .normalize('NFKC')
      .toLocaleLowerCase('ko-KR')
      .replace(/[^\p{L}\p{N}]+/gu, ' ')
      .trim();
    const compact = (value) => normalize(value).replace(/\s+/gu, '');

    const entries = cards.map((card) => ({
      card,
      search: compact(card.dataset.search || card.textContent),
      region: compact(card.dataset.region),
    }));
    const groupEntries = groups.map((group) => ({
      group,
      cards: Array.from(group.querySelectorAll('[data-branch-card]')),
    }));

    if (status) {
      status.setAttribute('aria-live', 'polite');
      status.setAttribute('aria-atomic', 'true');
      if (!status.hasAttribute('role')) status.setAttribute('role', 'status');
    }

    const filter = () => {
      const normalizedQuery = normalize(query.value);
      const terms = normalizedQuery ? normalizedQuery.split(/\s+/u) : [];
      const selectedRegion = region ? compact(region.value) : '';
      let count = 0;

      for (const entry of entries) {
        const regionMatches = !selectedRegion || entry.region === selectedRegion;
        const textMatches = terms.every((term) => entry.search.includes(term));
        const visible = regionMatches && textMatches;
        entry.card.hidden = !visible;
        if (visible) count += 1;
      }

      for (const entry of groupEntries) {
        entry.group.hidden = !entry.cards.some((card) => !card.hidden);
      }

      if (empty) empty.hidden = count !== 0;
      if (status) {
        const total = entries.length.toLocaleString('ko-KR');
        const matched = count.toLocaleString('ko-KR');
        status.textContent = terms.length || selectedRegion
          ? `전체 ${total}개 지점 중 ${matched}개가 검색되었습니다.`
          : `전체 ${total}개 지점을 확인할 수 있습니다.`;
      }
    };

    const clear = () => {
      query.value = '';
      if (region) region.value = '';
      composing = false;
      filter();
      query.focus();
    };

    query.addEventListener('compositionstart', () => { composing = true; });
    query.addEventListener('compositionend', () => {
      composing = false;
      filter();
    });
    query.addEventListener('input', (event) => {
      if (!composing && !event.isComposing) filter();
    });
    query.addEventListener('search', () => {
      if (!composing) filter();
    });
    query.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && !composing && !event.isComposing) {
        event.preventDefault();
        clear();
      }
    });

    if (region) region.addEventListener('change', filter);
    if (reset) reset.addEventListener('click', (event) => {
      event.preventDefault();
      clear();
    });
    if (form) {
      form.addEventListener('submit', (event) => {
        event.preventDefault();
        if (!composing) filter();
      });
      form.addEventListener('reset', (event) => {
        event.preventDefault();
        clear();
      });
    }

    filter();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize, { once: true });
  } else {
    initialize();
  }
})();
