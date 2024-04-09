window.addEventListener('DOMContentLoaded', (event) => {
    const applicationType = document.querySelector("#id_application_type");
    const showTemplateCountryRow = UTILS.getShowElementFunc("#template_country-wrapper");

    applicationType.addEventListener("change", function (e) {
        showTemplateCountryRow(e.target.value === "CFS");
    });
});
