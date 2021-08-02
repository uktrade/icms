window.addEventListener('load', (event) => {
  const countryOfOrigin = document.querySelector("#id_origin_country");
  const categoryDescription = document.querySelector("#category_commodity_group_description");

  // django-selects
  const categorySelect = $('#id_category_commodity_group').djangoSelect2();
  const commoditySelect = $('#id_commodity').djangoSelect2();

  const labelChanger = getLabelChanger();

  countryOfOrigin.addEventListener("change", (e) => {
    categorySelect.empty();
    commoditySelect.empty();
    categoryDescription.textContent = "";
  })

  categorySelect.on("change", (e) => {
    const category = e.target.value;

    labelChanger.changeGroupLabel(category)
    labelChanger.changeGroupUnitLabel(category)
    commoditySelect.empty();
  })
});


function getLabelChanger() {
  const categoryGroups = JSON.parse(
    document.querySelector("#category_commodity_groups").textContent
  );

  return {
    categoryGroups: categoryGroups,
    descriptionLabel: document.querySelector("#category_commodity_group_description"),
    unitLabel: document.querySelector("#commodity_units"),

    changeGroupLabel: function(category) {
      let newLabel = "";

      if (this.categoryGroups.hasOwnProperty(category)) {
        newLabel = this.categoryGroups[category].label;
      }
      this.descriptionLabel.textContent = newLabel;
    },

    changeGroupUnitLabel: function(category) {
      let newLabel = "";

      if (this.categoryGroups.hasOwnProperty(category)) {
        newLabel = this.categoryGroups[category].unit;
      }
      this.unitLabel.textContent = newLabel;
    },
  }

}
