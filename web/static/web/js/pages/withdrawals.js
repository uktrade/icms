document.addEventListener("DOMContentLoaded", function (event) { // doesn't work in IE8: https://caniuse.com/#feat=domcontentloaded
    "use strict";

    var dropdown = document.getElementById('id_status');

    var container = document.getElementsByClassName('row_id_response')[0];
    showOrHide(dropdown, container);

    dropdown.onchange = function () {
        showOrHide(dropdown, container);
    };

});

function showOrHide(dropdown, container) {
    "use strict";
    if (dropdown.options.length === 3) {
        dropdown.remove(0);
    }

    if (dropdown.selectedIndex === 0) {
        container.classList.add('hidden');
    } else {
        container.classList.remove('hidden');
    }
}
