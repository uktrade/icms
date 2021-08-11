window.addEventListener('load', (event) => {
  const commoditySelect = document.querySelector("#id_commodity");
  const labelChanger = getLabelChanger();

  commoditySelect.addEventListener("change", (e) => {
    const newCommodity = parseInt(e.target.value);
    labelChanger.changeCommodityUnitLabel(newCommodity)
  });

});


function getLabelChanger() {
  const commodityGroupData = JSON.parse(
    document.querySelector("#commodity_group_data").textContent
  );

  return {
    commodityGroupData: commodityGroupData,
    unitLabel: document.querySelector("#commodity_unit_description"),

    changeCommodityUnitLabel: function (commodity) {
      let newLabel = "";
      for (const [group_pk, group_data] of Object.entries(commodityGroupData)) {

        if (group_data.group_commodities.includes(commodity)) {
          newLabel = group_data.unit_description;
          break;
        }
      }
      this.unitLabel.textContent = newLabel;
    }
  }
}
