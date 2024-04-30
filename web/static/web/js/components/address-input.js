window.addEventListener('load', (event) => {
  const addressEntries = document.querySelectorAll("div[name='address_entry_form']");

  addressEntries.forEach((node) => {
    const addressTypeSearch = node.querySelector("div[name='address_type_field'] input[value='SEARCH']");
    const addressTypeManual = node.querySelector("div[name='address_type_field'] input[value='MANUAL']");
    const addressInput = node.querySelector("div[name='address_field'] textarea");
    const postcodeInputDiv = node.querySelector("div[name='postcode_field'] div.input-group");
    const postcodeInput = node.querySelector("div[name='postcode_field'] input");
    const selectAddressWrapper = node.querySelector("div[name='row_available_addresses']")
    const selectAddress = node.querySelector("select[name='available_addresses']");

    // value of select when doing a lookup.
    const SEARCH = "SEARCH"

    // used to delay api search
    let postcodeSearchDelay;

    // Setup listeners
    addressTypeSearch.addEventListener("change", (e) => {
      clearTimeout(postcodeSearchDelay);
      let checked = e.target.checked;

      // Set readonly depending on search type.
      addressInput.readOnly = checked;
    });

    addressTypeManual.addEventListener("change", (e) => {
      clearTimeout(postcodeSearchDelay);
      let checked = e.target.checked;

      // Set readonly depending on search type.
      addressInput.readOnly = !checked;

      if (checked) {
        setAddressSelectDisplay(selectAddressWrapper, "none")
      }
    });

    postcodeInput.addEventListener("keyup", (e) => {
      clearTimeout(postcodeSearchDelay);

      postcodeSearchDelay = setTimeout(() => {
        const postcode = postcodeInput.value;
        if (addressTypeManual.checked) {
          return;
        }

        if (postcode === "") {
          return;
        }

        postcodeLookup(postcode).then((response) => {
          response.json().then(results => {
            clearErrors(postcodeInputDiv);

            if (response.ok) {
              setAddressSelectDisplay(selectAddressWrapper, "block")
              processAddressOptions(selectAddress, results);
            } else {
              setAddressSelectDisplay(selectAddressWrapper, "none")
              processError(postcodeInputDiv, results);
            }
          });
        });
      }, 750);
    });

    selectAddress.addEventListener("change", (e) => {
      if (addressTypeManual.checked) {
        return;
      }
      addressInput.value = e.target.value;
    });
  });
});


function setAddressSelectDisplay(selectAddressWrapper, displayVal) {
  selectAddressWrapper.style.display = displayVal
}


function processAddressOptions(choicesSelect, results) {
  // reset the choices if present
  choicesSelect.length = 0

  // Iterate over the results to create the available choices
  choicesSelect[0] = new Option("Please choose an address", "")

  results.forEach((address, idx) => {
    let formatted_address = address["formatted_address"].filter((x) => x !== "")
    let text = formatted_address.join(" ")
    let value = formatted_address.join("\n")

    choicesSelect[idx + 1] = new Option(text, value)
  });
}

function processError(postcodeInputDiv, results) {
  postcodeInputDiv.classList.add("input-error")
  postcodeInputDiv.appendChild(
    createErrorDiv("postcode-error-div", results["error_msg"])
  );

  // Log an optional dev error message.
  if (results.hasOwnProperty("dev_error_msg")) {
    console.log(results["dev_error_msg"])
  }
}


function createErrorDiv(name, errorMsg) {
  let errorDiv = document.createElement("DIV");
  errorDiv.setAttribute("name", name);
  errorDiv.classList.add("error-message");
  errorDiv.appendChild(document.createTextNode(errorMsg));

  return errorDiv
}

function clearErrors(postcodeInputDiv) {
  const errorDiv = postcodeInputDiv.querySelector("div[name='postcode-error-div']");
  postcodeInputDiv.classList.remove("input-error");

  if (errorDiv !== null) {
    errorDiv.remove();
  }
}
