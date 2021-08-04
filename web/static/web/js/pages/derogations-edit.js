window.addEventListener('load', (event) => {
  const countryOfOrigin = $('#id_origin_country').djangoSelect2();
  const countryOfConsignment = document.querySelector("#id_consignment_country");
  const furtherDetails = document.querySelector("#further-details-wrapper");
  const requestPurpose = document.querySelector("#id_purpose_of_request");
  const civDetailsWrapper = document.querySelector("#civilian-purpose-details-wrapper");
  const civDetails = document.querySelector("#id_civilian_purpose_details");

  const syriaValue = getSyriaValue(countryOfConsignment);

  countryOfOrigin.on("change", (e) => {
    const newCountry = e.target.value;
    const otherCountry = countryOfConsignment.value;

    showFurtherDetails(furtherDetails, newCountry, otherCountry, syriaValue)
  });

  countryOfConsignment.addEventListener("change", (e) => {
    const newCountry = e.target.value;
    const otherCountry = countryOfOrigin.val();

    showFurtherDetails(furtherDetails, newCountry, otherCountry, syriaValue)
  });

  requestPurpose.addEventListener("change", (e) => {
    const purpose = e.target.value;

    if (purpose === "OCP") {
      civDetailsWrapper.style.display = "block"
    } else {
      civDetails.value = "";
      civDetailsWrapper.style.display = "none"
    }
  });
});


function getSyriaValue(countrySelect) {
  for (let i = 0; i < countrySelect.length; i++) {
    let country = countrySelect.options[i];

    if (country.textContent === "Syria") {
      return country.value;
    }
  }

  return null;
}


/**
 * We need to check both country selects to see if either of them are syria
 */
function showFurtherDetails(furtherDetailsWrapper, countryChanged, otherSelectValue, syriaVal) {
  const showFD =  countryChanged === syriaVal || otherSelectValue === syriaVal

  furtherDetailsWrapper.style.display = showFD ? "block": "none";
}
