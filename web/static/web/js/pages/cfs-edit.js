window.addEventListener('DOMContentLoaded', (event) => {
  const countrySelect2 = $("#id_countries").djangoSelect2();
  const events = new EditCFSEventHandler(countrySelect2);

  countrySelect2.on("change", (e) => {
    events.countrysOnChange(e);
  });

  showBannerOnLoad();
});

class EditCFSEventHandler {
  constructor(countrySelect2) {
    this.countrySelect2 = countrySelect2;
    this.countryConfig = JSON.parse(document.querySelector("#country_config").textContent);
  }

  countrysOnChange(e) {
    const selectedCountries = this.countrySelect2.val();
    updateCPTPPInfo(selectedCountries, this.countryConfig);
  }

}

/**
 * Show or hide the CPTPP banner and updates the selected country names in the banner.
 *
 * @param {Array.<string>} selectedCountries List of selected countries
 * @param {Object.<string, string>} config
 */
function updateCPTPPInfo(selectedCountries, countryConfig) {
  const wrapper = document.querySelector("#cptpp-banner");
  const cptppCountryText = getCPTPPCountryText(selectedCountries, countryConfig);
  const isCPTPP = cptppCountryText !== undefined;

  if (wrapper) {
    wrapper.style.display = isCPTPP ? "block" : "none";
    const selectedCountrySpan = wrapper.querySelector("#selected-cptpp");
    selectedCountrySpan.textContent = cptppCountryText;
  }
}

/**
 * Return a string listing the selected CPTPP country names.
 *
 * @param {Array.<string>} countries List of selected countries
 * @param {Object.<string, string>} config
 */
function getCPTPPCountryText(countries, config) {
  let countryArray = [];

  for (const country of countries) {
    if (config.hasOwnProperty(country)) {
      countryArray.push(config[country]);
    }
  }

  if (countryArray.length == 0) {
    return undefined;
  }

  if (countryArray.length == 1) {
    return countryArray.at(0)
  }

  countryArray = countryArray.sort()
  const textStart = countryArray.slice(0, -1).join(", ");
  const textEnd = countryArray.at(-1);

  return textStart + " and " + textEnd;
}

/**
 * Shows the CPTPP banner if CPTPP countries are already selected on page load.
 */
function showBannerOnLoad() {
  const selectedCountries = [];
  const selections = $("#id_countries").select2("data");

  if (selections.length == 0) {
    return;
  }

  for (const country of selections) {
    selectedCountries.push(country.id);
  }

  const countryConfig = JSON.parse(document.querySelector("#country_config").textContent);
  updateCPTPPInfo(selectedCountries, countryConfig);
}
