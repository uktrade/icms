document.addEventListener("DOMContentLoaded", function (event) { // doesn't work in IE8: https://caniuse.com/#feat=domcontentloaded
    "use strict";

    document.getElementsByTagName('form')[0].addEventListener("submit", function (event) {
        var dropdown = document.getElementById('id_response');
        var reason = document.getElementById('id_response_reason');

        if (dropdown.options.length === 2 && dropdown.selectedIndex !== 1 || reason.value !== '') {
            showModal();
        }
        event.preventDefault();
    });

    doRemoveOptionalLabels();

    var dropdown = document.getElementById('id_response');

    var container = document.getElementById('response-reason-container');

    dropdown.onchange = function () {
        showOrHide(dropdown, container);

        doRemoveOptionalLabels();
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

        doRemoveOptionalLabels();
    }
}

function doRemoveOptionalLabels() {
    "use strict";
    removeOptionalLabels();
    removeOptionalLabels(); // needs two calls, for some unknown reason, to fully do the job ...
}

function removeOptionalLabels() {
    "use strict";
    var optionalTags = document.getElementsByClassName("mand-label");
    for (var i = 0; i < optionalTags.length; i++) {
        optionalTags[i].parentNode.removeChild(optionalTags[i]);
    }
}

function showModal(event) {
    "use strict";

    var html = '<div class="modal-popover-container">' +
        '<div class="modal-popover small-popover modal-alert-confirm">' +
        '<div class="modal-popover-content" role="alertdialog">' +
        '<div class="modal-popover-icon icon-question"></div>' +
        '<div class="modal-popover-text">Are you sure you want to close this Access Request? This will email the requester with the status below.</div>' +
        '<ul class="modal-popover-actions"><li><button class="primary-button alert-dismiss" ' +
        'onclick="javascript:hideModal(); submit();">OK</button></li><li>' +
        '<button class="link-button" onclick="hideModal()">Cancel</button></li></ul></div></div></div>';

    var div = document.createElement('div');

    div.innerHTML = html;

    document.body.insertBefore(div, document.body.firstChild);
}

function hideModal() {
    "use strict";
    document.body.removeChild(document.body.firstChild);
}

function submit() {
    "use strict";

    var dropdown = document.getElementById('id_response');

    if (dropdown.selectedIndex === 0) {
        var reason = document.getElementById('id_response_reason');
        reason.value = '';
    }

    document.getElementsByTagName('form')[0].submit();
}