window.addEventListener('load', (event) => {
  const productRawMaterial = document.querySelector("#id_any_raw_materials");
  const endUse = document.querySelector('#final-product-end-use-wrapper');

  const setEndUse = (value) => {
    endUse.style.display = value === "yes" ? "block": "none";
  }

  // set initial value
  setEndUse(productRawMaterial.value);

  // Setup listeners
  productRawMaterial.addEventListener("change", (e) => {
    setEndUse(e.target.value);
  });
});
