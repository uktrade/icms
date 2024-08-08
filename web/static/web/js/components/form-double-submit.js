/*

Prevent double submit for <form> elements.

On page load, install a handler for <form method="POST" class="double-submit">
elements.

*/
'use strict';

const formBlocked = 'double-submit-blocked';

const blockDoubleSubmit = function(event) {
    let form = event.target;

    if (form.classList.contains(formBlocked)) {
        event.preventDefault();
        return;
    }

    form.classList.add(formBlocked);
};

window.addEventListener('load', function() {
    // Add event handler to all form submissions preventing double submission
    let forms = this.document.getElementsByTagName("form")
    Array.from(forms).forEach(function(el) {
        // Form.method is normalized, i.e. <form method='POST'> === 'post'.
        if (el.method === 'post') {
            el.addEventListener('submit', blockDoubleSubmit);
        }
    });
});
