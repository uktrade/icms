window.addEventListener('load', (event) => {
  // How to initialise the django-select-2 instance in JS
  const commoditySelect = $('#id_cp_commodities').djangoSelect2();
  const category = document.querySelector("#id_cp_category");

  const changeCommodityLabel = makeChangeCommodityLabel();

  // When the category changes the commodities should be cleared as they aren't valid.
  category.addEventListener("change", (e) => {
    const category = e.target.value;

    changeCommodityLabel(category)
    commoditySelect.empty();
  });
});


function makeChangeCommodityLabel() {
  // object where key=category, value=category description
  const categoryDescriptions = JSON.parse(
    document.querySelector("#category_descriptions").textContent
  );
  const categoryDescriptionLabel = document.querySelector("#cp_category_description");

  function changeCommodityLabel(category) {
    let newLabel = "";

    if (categoryDescriptions.hasOwnProperty(category)) {
      newLabel = categoryDescriptions[category];
    }
    categoryDescriptionLabel.textContent = newLabel;
  }

  return changeCommodityLabel;
}
