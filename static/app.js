(() => {
  const body = document.body;
  const openMenu = () => body.classList.add('menu-open');
  const closeMenu = () => body.classList.remove('menu-open');

  document.querySelectorAll('[data-menu-open]').forEach((button) => button.addEventListener('click', openMenu));
  document.querySelectorAll('[data-menu-close]').forEach((button) => button.addEventListener('click', closeMenu));
  window.addEventListener('resize', () => {
    if (window.innerWidth > 980) closeMenu();
  });

  document.querySelectorAll('[data-flash-close]').forEach((button) => {
    button.addEventListener('click', () => button.closest('.flash')?.remove());
  });

  const checklist = document.querySelector('[data-study-checklist]');
  if (checklist) {
    const storageKey = checklist.dataset.studyChecklist;
    const checks = [...checklist.querySelectorAll('[data-study-step]')];
    let saved = {};
    try {
      saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
    } catch (_error) {
      saved = {};
    }

    const updateProgress = () => {
      const complete = checks.filter((item) => item.checked).length;
      const total = checks.length;
      const percent = total ? Math.round((complete / total) * 100) : 0;
      checklist.querySelectorAll('[data-study-progress-text]').forEach((node) => {
        node.textContent = `${complete} of ${total} steps complete`;
      });
      checklist.querySelectorAll('[data-study-progress-bar]').forEach((node) => {
        node.style.width = `${percent}%`;
      });
      const state = {};
      checks.forEach((item) => { state[item.value] = item.checked; });
      try { localStorage.setItem(storageKey, JSON.stringify(state)); } catch (_error) { /* no-op */ }
    };

    checks.forEach((item) => {
      item.checked = Boolean(saved[item.value]);
      item.addEventListener('change', updateProgress);
    });
    updateProgress();
  }

  const rubric = document.querySelector('[data-rubric-form]');
  if (rubric) {
    const inputs = [...rubric.querySelectorAll('[data-rubric-score]')];
    const totalNode = rubric.querySelector('[data-rubric-total]');
    const updateTotal = () => {
      const total = inputs.reduce((sum, input) => {
        const value = Number.parseFloat(input.value);
        return sum + (Number.isFinite(value) ? value : 0);
      }, 0);
      if (totalNode) totalNode.textContent = total.toFixed(total % 1 ? 1 : 0);
    };
    inputs.forEach((input) => input.addEventListener('input', updateTotal));
    updateTotal();
  }

  document.querySelectorAll('[data-confirm]').forEach((element) => {
    element.addEventListener('click', (event) => {
      if (!window.confirm(element.dataset.confirm)) event.preventDefault();
    });
  });
})();
