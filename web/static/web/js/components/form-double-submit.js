/*

Prevent double submit for <form> elements.

On page load, install a handler for <form method="POST" class="double-submit">
elements.

*/
'use strict';

const doubleSubmitClass = {
    formSelector: 'no-double-submit',
    formBlocked: 'double-submit-blocked'
};

const blockDoubleSubmit = function(event) {
    let form = event.target;

    if (form.classList.contains(doubleSubmitClass.formBlocked)) {
        event.preventDefault();
        return;
    }

    form.classList.add(doubleSubmitClass.formBlocked);
};

window.addEventListener('load', function() {
    let elements = this.document.getElementsByClassName(doubleSubmitClass.formSelector);

    Array.from(elements).forEach(function(el) {
        // Form.method is normalized, i.e. <form method='POST'> === 'post'.
        if (el.method === 'post') {
            el.addEventListener('submit', blockDoubleSubmit);
        }
    });
});
