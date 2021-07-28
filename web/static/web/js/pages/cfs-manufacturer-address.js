window.addEventListener('load', (event) => {
  const addressType = document.querySelector("#id_manufacturer_address_entry_type");
  const manufacturerAddress = document.querySelector("#id_manufacturer_address");
  const manufacturerPostcode = document.querySelector("#id_manufacturer_postcode");
  const selectAddress = document.querySelector("#id_available_addresses");

  // value of select when doing a lookup.
  const SEARCH = "S"

  // used to delay api search
  let postcodeSearchDelay;

  // Setup listeners
  addressType.addEventListener("change", (e) => {
    clearTimeout(postcodeSearchDelay);
    let type = e.target.value;

    // Set readonly depending on search type.
    manufacturerAddress.readOnly = type === SEARCH

    if (type !== "search") {
      setAddressSelectDisplay("none")
    }
  });

  manufacturerPostcode.addEventListener("keyup", (e) => {
    clearTimeout(postcodeSearchDelay);

    postcodeSearchDelay = setTimeout(() => {
      const postcode = manufacturerPostcode.value;
      if (addressType.value !== SEARCH) {
        return;
      }

      if (postcode === "") {
        return;
      }

      postcodeLookup(postcode).then((response) => {
        response.json().then(results => {
          clearErrors();

          if (response.ok) {
            setAddressSelectDisplay("block")
            processAddressOptions(results);
          } else {
            setAddressSelectDisplay("none")
            processError(results);
          }
        });
      });
    }, 750);
  });

  selectAddress.addEventListener("change", (e) => {
    if (addressType.value !== SEARCH) {
      return;
    }
    manufacturerAddress.value = e.target.value;
  });
});


function setAddressSelectDisplay(displayVal) {
  const selectAddressWrapper = document.querySelector("#row_id_available_addresses");
  selectAddressWrapper.style.display = displayVal
}


function processAddressOptions(results) {
  const choicesSelect = document.querySelector("#id_available_addresses");

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

function processError(results) {
  let postcodeInputDiv = document.querySelector(".row_id_manufacturer_postcode div.input-group")

  postcodeInputDiv.classList.add("input-error")
  postcodeInputDiv.appendChild(
    createErrorDiv("postcode-error-div", results["error_msg"])
  );

  // Log an optional dev error message.
  if (results.hasOwnProperty("dev_error_msg")) {
    console.log(results["dev_error_msg"])
  }
}


function createErrorDiv(id, errorMsg) {
  let errorDiv = document.createElement("DIV");
  errorDiv.id = id
  errorDiv.classList.add("error-message")
  errorDiv.appendChild(document.createTextNode(errorMsg));

  return errorDiv
}

function clearErrors() {
  let postcodeInputDiv = document.querySelector(".row_id_manufacturer_postcode div.input-group")
  const errorDiv = document.querySelector("#postcode-error-div")
  postcodeInputDiv.classList.remove("input-error")

  if (errorDiv !== null) {
    errorDiv.remove()
  }
}
