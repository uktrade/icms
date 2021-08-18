

window.addEventListener('load', (event) => {
  const radios = document.querySelectorAll('input[type=radio][name="gmp_certificate_issued"]');
  const isoFieldsWrapper = document.querySelector("#iso-fields-wrapper");

  radios.forEach((radio) => radio.addEventListener('change', (e) => {
    setIsoDisplay(isoFieldsWrapper, e.target.value);
  }));

})


function setIsoDisplay(wrapper, value) {
  wrapper.style.display = value === "ISO_22716" ? "block" : "none";
}
