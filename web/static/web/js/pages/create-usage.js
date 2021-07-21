window.addEventListener('load', (event) => {
  const appTypeSelect = document.querySelector("#id_application_type");
  const countrySelect = $('#id_country').djangoSelect2();

  // Clear the countries when the application type changes.
  appTypeSelect.addEventListener("change", (e) => {
    countrySelect.empty();
  });
});
