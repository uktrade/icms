window.addEventListener('load', (event) => {
  "use strict";

  const showBoughtFrom = UTILS.getShowElementFunc("#know-bought-from-info-box")
  const boughtFromRadios = document.querySelectorAll("input[type=radio][name=know_bought_from]")

  boughtFromRadios.forEach((radio) => radio.addEventListener("change", (e) => {
    showBoughtFrom(e.target.value.toLowerCase() === "false")
  }));
});
