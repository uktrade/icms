window.addEventListener("DOMContentLoaded", function (event) { // doesn't work in IE8: https://caniuse.com/#feat=domcontentloaded
    "use strict";

    var dropdown = document.getElementById('id_group_type');

    var container = document.getElementsByClassName('row_id_commodities')[0];
    showOrHide(dropdown, container);

    dropdown.onchange = function () {
        showOrHide(dropdown, container);
    };

});

function showOrHide(dropdown, container) {
    "use strict";
    if (dropdown.value === "" || dropdown.value === "AUTO") {
        container.classList.add('hidden');
    } else {
        container.classList.remove('hidden');
    }
}
