window.addEventListener('load', (event) => {
  const countryOfOrigin = document.querySelector("#id_origin_country");
  const categoryDescription = document.querySelector("#category_commodity_group_description");
  const quantity = document.querySelector("#id_quantity");

  // django-selects
  const categorySelect = $('#id_category_commodity_group').djangoSelect2();
  const commoditySelect = $('#id_commodity').djangoSelect2();

  const labelChanger = getLabelChanger();
  const maximumAllocation = getMaximumAllocation();

  countryOfOrigin.addEventListener("change", (e) => {
    categorySelect.empty();
    commoditySelect.empty();
    categoryDescription.textContent = "";

    maximumAllocation.triggerChange(quantity);
  })

  categorySelect.on("change", (e) => {
    const category = e.target.value;

    labelChanger.changeGroupLabel(category);
    labelChanger.changeGroupUnitLabel(category);
    commoditySelect.empty();

    maximumAllocation.triggerChange(quantity);
  });

  quantity.addEventListener("change", (e) => {
    const category = document.querySelector("#id_category_commodity_group").value;
    const country = document.querySelector("#id_origin_country").value;

    maximumAllocation.displayWarning(category, country);

  });
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


function getMaximumAllocation() {
  const usages = JSON.parse(
    document.querySelector("#max_allocation_usages").textContent
  );

  return {
    usages: usages,
    maxAllocationInfoBox: document.querySelector("#max-allocation-info-box"),
    maxAllocationValue: document.querySelector("#max-allocation-value"),

    displayWarning: function(category, country) {
      const quantity = parseFloat(document.querySelector("#id_quantity").value);
      let maxAllocation = null;
      if (this.usages.hasOwnProperty(category) && this.usages[category].hasOwnProperty(country)) {
        maxAllocation = this.usages[category][country];
      }

      if (!isNaN(quantity) && maxAllocation != null && quantity > maxAllocation) {
        this.maxAllocationInfoBox.style.display = "block";
        this.maxAllocationValue.textContent = maxAllocation;
      } else {
        this.maxAllocationInfoBox.style.display = "none";
        this.maxAllocationValue.textContent = "";
      }
    },

    triggerChange: function(quantity, category, country) {
      const changeEvent = new Event("change");
      quantity.dispatchEvent(changeEvent);
    }
  }
}
