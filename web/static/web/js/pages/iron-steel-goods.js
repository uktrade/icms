window.addEventListener('load', (event) => {
  const importer = document.querySelector('#id_origin_country');
  const categoryDescription = document.querySelector("#category_commodity_group_description");

  const categorySelect2 = $("#id_category_commodity_group").djangoSelect2();
  const commoditySelect2 = $("#id_commodity").djangoSelect2();

   importer.addEventListener("change", (e) => {
    categorySelect2.empty();
    commoditySelect2.empty();
    categoryDescription.textContent = "";
   });

  const labelChanger = getLabelChanger();

  categorySelect2.on("change", (e) => {
    const category = e.target.value;

    labelChanger.changeGroupLabel(category)

    commoditySelect2.empty();
  })
});

function getLabelChanger() {
  const categoryGroups = JSON.parse(
    document.querySelector("#category_commodity_groups").textContent
  );

  return {
    categoryGroups: categoryGroups,
    descriptionLabel: document.querySelector("#category_commodity_group_description"),

    changeGroupLabel: function(category) {
      let newLabel = "";

      if (this.categoryGroups.hasOwnProperty(category)) {
        newLabel = this.categoryGroups[category].label;
      }
      this.descriptionLabel.textContent = newLabel;
    },
  }

}

