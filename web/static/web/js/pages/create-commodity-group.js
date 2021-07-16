window.addEventListener("DOMContentLoaded", function (event) { // doesn't work in IE8: https://caniuse.com/#feat=domcontentloaded
    "use strict";

    const dropdownSelect = document.getElementById('id_group_type');
    const commodityTypeSelect = document.querySelector("#id_commodity_type");
    const commoditySelect = $('#id_commodities').djangoSelect2();
    const commodities = document.getElementsByClassName('row_id_commodities')[0];
    const unit = document.getElementsByClassName('row_id_unit')[0];

    showOrHide(dropdownSelect, commodities, unit);

    dropdownSelect.onchange = function () {
        showOrHide(dropdownSelect, commodities, unit);
    };

    // When the type changes the commodities must be cleared.
    commodityTypeSelect.addEventListener("change", (e) => {
        commoditySelect.empty();
    });

});

function showOrHide(dropdown, commodities, unit) {
    "use strict";
    if (dropdown.value === "" || dropdown.value === "AUTO") {
        commodities.classList.add('hidden');
        unit.classList.add('hidden');
    } else {
        commodities.classList.remove('hidden');
        unit.classList.remove('hidden');
    }
}
