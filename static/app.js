(() => {
  const body = document.body;
  const open = document.querySelector('[data-open-menu]');
  const close = document.querySelector('[data-close-menu]');
  if (open) open.addEventListener('click', () => body.classList.add('menu-open'));
  if (close) close.addEventListener('click', () => body.classList.remove('menu-open'));
  document.querySelectorAll('[data-dismiss]').forEach((button) => {
    button.addEventListener('click', () => button.closest('.flash')?.remove());
  });
  setTimeout(() => document.querySelectorAll('.flash').forEach((item) => item.remove()), 6000);
})();
