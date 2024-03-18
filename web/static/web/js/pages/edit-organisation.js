/**
 * Event handler for the submit button on the edit importer/exporter page
 */
(function ($) {
    window.addEventListener('load', (event) => {

        document.getElementById('save-button').addEventListener('click', (event) => {
            editImporterExporterOnSubmitHandler(event)
        });

        document.getElementById('id_registered_number').addEventListener('change', (event) => {
            document.getElementById('edit-form').dataset.companyNumberChanged = "true";
        })
    });
})(jQuery)


/**
 * Submits the edit form
 */
function submitEditForm() {
    document.getElementById('edit-form').submit()
}

/**
 * Event handler for the submit button on the edit importer/exporter page
 * Checks if the company number is valid and if it is not found on Companies House, if not,
 * a dialogue is shown to confirm the user's intention
 * @param {Event} event
 */
function editImporterExporterOnSubmitHandler(event) {
    if (!document.getElementById('edit-form').dataset.companyNumberChanged === "true" || !document.getElementById('edit-form').dataset.companyNumberChanged) {
        // the company number hasn't changed, no need to check it
        return;
    }

    event.preventDefault();

    const company_number = document.getElementById('id_registered_number').value
    getCompanyFromCompaniesHouse(company_number).then(response => {
        if (response.status === 404) {
            const d = Dialogue();
            const message = "Registered number not found on Companies House, are you sure you want to continue?";
            d.show(message, submitEditForm);
        } else {
            submitEditForm()
        }
    })
}
