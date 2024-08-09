'use strict';

window.addEventListener('load', function () {
    const formsets = document.getElementsByClassName("formset-container");

    Array.from(formsets).forEach(function (el) {
        let df = new DynamicFormset(el);
        df.setupEventHandlers();
    });

});


class DynamicFormset {
    constructor(el) {
        this.formset = el;
        this.prefix = el.dataset.formsetPrefix;
        this.totalFormsSelector = el.querySelector(`input[name="${this.prefix}-TOTAL_FORMS"]`);
        this.initialFormsSelector = el.querySelector(`input[name="${this.prefix}-INITIAL_FORMS"]`);
        this.minNumFormsSelector = el.querySelector(`input[name="${this.prefix}-MIN_NUM_FORMS"]`);
        this.maxNumFormsSelector = el.querySelector(`input[name="${this.prefix}-MAX_NUM_FORMS"]`);
        this.emtpyForm = el.querySelector(`#${this.prefix}-hidden`);
    }

    setupEventHandlers() {
        let button = this.formset.querySelector(`.${this.prefix}-formset-add-form`);

        button.addEventListener("click", (e) => {
            e.preventDefault();

            this.addForm();
        });

        // Setup remove buttons:
        const removeButtons = this.formset.querySelectorAll(`.${this.prefix}-formset-remove-form`);
        Array.from(removeButtons).forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                this.removeForm(btn);
            });
        });
    }

    totalForms() {
        return this.totalFormsSelector.value * 1;
    }

    maxForms() {
        return this.maxNumFormsSelector.value * 1;
    }

    hasNestedFormsets() {
        return this.formset.dataset.nestedFormsets === "true";
    }

    addForm() {
        if (this.totalForms() >= this.maxForms()) {
            console.warn("Unable to add another form as max forms reached.");
            return;
        }

        // Duplicate empty form.
        let newForm = this.emtpyForm.cloneNode(true);
        // Remove hidden style display property
        newForm.style.removeProperty("display");

        // Update all references to -__prefix__- in the element names
        let newValue = this.totalFormsSelector.value;

        let matchValue = this.prefix + '-__prefix__-';
        let match = new RegExp(matchValue);
        let replace = this.prefix + "-" + newValue.toString() + "-";

        // List of element attributes that need "-__prefix__-" replacing
        ['id', 'for', 'name', 'data-formset-prefix', 'class'].forEach(function (attr) {
            newForm.querySelectorAll('[' + attr + '*=' + matchValue + ']').forEach(function (el) {
                el.setAttribute(attr, el.getAttribute(attr).replace(match, replace));
            });
        });

        // Add form to dom
        this.formset.querySelector(".forms").insertAdjacentElement("beforeend", newForm);

        // Increment total forms.
        this.totalFormsSelector.value = this.totalForms() + 1;

        if (this.hasNestedFormsets()) {
            const formsets = newForm.getElementsByClassName("formset-container");

            Array.from(formsets).forEach(function (el) {
                let df = new DynamicFormset(el);
                df.setupEventHandlers();
            });
        }
    }

    removeForm(deleteBtn) {
        // Set the hidden input to checked so it will get removed.
        const buttonId = deleteBtn.dataset.buttonId;
        this.formset.querySelector(`#${buttonId}`).checked = true;

        // Hide the row
        deleteBtn.closest('.formset-form').classList.add('hidden');
    }
}
