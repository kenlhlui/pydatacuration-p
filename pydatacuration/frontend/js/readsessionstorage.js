document.addEventListener('DOMContentLoaded', () => {
  // Handle all auto-populate elements - both form fields and display elements
  const fields = document.querySelectorAll('input[name], textarea[name], select[name]');
  const displayElements = document.querySelectorAll('.auto-populate[data-key]');
  
  console.log('Found form fields:', fields);
  console.log('Found display elements:', displayElements);

  // Handle form fields (inputs, textareas, selects)
  fields.forEach((el) => {
    const key = el.name;
    // 1) load saved value (if any)
    const saved = sessionStorage.getItem(key);
    if (saved !== null) {
      el.value = saved;
      el.classList.add('auto-populate');
    }
    // 2) watch for changes and save
    el.addEventListener('input', () => {
      sessionStorage.setItem(key, el.value);
      console.log(`Saved ${key} to sessionStorage:`, el.value);
    });
  });

  // Handle display elements (spans with data-key)
  displayElements.forEach((element) => {
    const key = element.dataset.key;
    const value = sessionStorage.getItem(key) || 'Not set';
    element.textContent = value;
    console.log(`Populated display element ${key} with:`, value);
  });
});
