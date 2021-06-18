window.addEventListener('load', (event) => {
  // How to initialise the django-select-2 instance in JS
  const commoditySelect = $('#id_cp_commodities').djangoSelect2();
  const category = document.querySelector("#id_cp_category");

  // When the category changes the commodities should be cleared as they aren't valid.
  category.addEventListener("change", () => {
    commoditySelect.empty();
  });
});

