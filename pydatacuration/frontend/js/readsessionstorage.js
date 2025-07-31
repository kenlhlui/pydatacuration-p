document.addEventListener('DOMContentLoaded', () => {
  // 1) Find every field you want to auto-sync
  const autoFields = document.querySelectorAll(
    'input.auto-populate[name], textarea.auto-populate[name], select.auto-populate[name]'
  );

  autoFields.forEach((el) => {
    const key = el.name;

    // 2) Load from sessionStorage (if present)
    const saved = sessionStorage.getItem(key);
    if (saved !== null) {
      el.value = saved;
      el.classList.add('pre-filled');
    }
    // 3) On user edit, write back to sessionStorage
    const save = () => sessionStorage.setItem(key, el.value);
    el.addEventListener('input', save);
    if (el.tagName === 'SELECT') {
      el.addEventListener('change', save);
    }
  });
});
