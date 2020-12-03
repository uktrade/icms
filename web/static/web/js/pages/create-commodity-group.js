window.addEventListener("DOMContentLoaded", function (event) { // doesn't work in IE8: https://caniuse.com/#feat=domcontentloaded
    "use strict";

    var dropdown = document.getElementById('id_group_type');

    var commodities = document.getElementsByClassName('row_id_commodities')[0];
    var unit = document.getElementsByClassName('row_id_unit')[0];
    showOrHide(dropdown, commodities, unit);

    dropdown.onchange = function () {
        showOrHide(dropdown, commodities, unit);
    };

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
