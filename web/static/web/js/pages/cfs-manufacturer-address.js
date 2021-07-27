window.addEventListener('load', (event) => {
  const addressType = document.querySelector("#id_manufacturer_address_entry_type");
  const manufacturerAddress = document.querySelector("#id_manufacturer_address");
  const manufacturerPostcode = document.querySelector("#id_manufacturer_postcode");
  let postcodeSearchDelay;

  // Setup listeners
  addressType.addEventListener("change", (e) => {
    clearTimeout(postcodeSearchDelay);
    let type = e.target.value;

    // Set readonly depending on search type.
    manufacturerAddress.readOnly = type === "S"
  });

  manufacturerPostcode.addEventListener("keyup", (e) => {
    clearTimeout(postcodeSearchDelay);

    postcodeSearchDelay = setTimeout(() => {
      if (addressType.value === "M") {
        return;
      }
      console.log("Add postcode lookup here...");
    }, 1000);
  });
});
