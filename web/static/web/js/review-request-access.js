document.addEventListener("DOMContentLoaded", function (event) { // doesn't work in IE8: https://caniuse.com/#feat=domcontentloaded
    "use strict";

    // document.getElementsByName('_start')[0].addEventListener("click", showModal);
    document.getElementsByTagName('form')[0].addEventListener("submit", function (event) {
        showModal(event)
        event.preventDefault();
    });

});

function showModal(event) {
    "use strict";

    var html = '<div class="modal-popover-container">' +
        '<div class="modal-popover small-popover modal-alert-confirm">' +
        '<div class="modal-popover-content" role="alertdialog">' +
        '<div class="modal-popover-icon icon-question"></div>' +
        '<div class="modal-popover-text">Are you sure you want to close this Access Request? This will email the requester with the status below.</div>' +
        '<ul class="modal-popover-actions"><li><button class="primary-button alert-dismiss" ' +
        'onclick="javascript:hideModal(); document.getElementsByTagName(\'form\')[0].submit();">OK</button></li><li>' +
        '<button class="link-button" onclick="hideModal()">Cancel</button></li></ul></div></div></div>';

    var div = document.createElement('div');

    div.innerHTML = html;

    document.body.insertBefore(div, document.body.firstChild);
}

function hideModal() {
    "use strict";
    document.body.removeChild(document.body.firstChild);
}