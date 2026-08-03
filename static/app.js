(() => {
  const body = document.body;
  document.querySelectorAll('[data-open-menu]').forEach((button) => button.addEventListener('click', () => body.classList.add('menu-open')));
  document.querySelectorAll('[data-close-menu]').forEach((item) => item.addEventListener('click', () => body.classList.remove('menu-open')));
  document.querySelectorAll('[data-dismiss]').forEach((button) => button.addEventListener('click', () => button.closest('.flash')?.remove()));
  document.querySelectorAll('[data-select-all-students]').forEach((toggle) => {
    toggle.addEventListener('change', () => {
      const fieldset = toggle.closest('fieldset');
      fieldset?.querySelectorAll('input[name="student_ids"]').forEach((box) => { box.checked = toggle.checked; });
    });
  });
  setTimeout(() => document.querySelectorAll('.flash').forEach((item) => item.remove()), 7000);
})();
