"use strict";

window.addEventListener('load', function (event) {
  setupSection58OtherEventHandler(); // /PS-IGNORE
});


/**
 * Function to show/ hide section 58 description
 */
function setupSection58OtherEventHandler() { // /PS-IGNORE
  const showSec58OtherDesc = UTILS.getShowElementFunc("#other-description-wrapper"); // /PS-IGNORE

  // Form field to watch
  const section58Other = document.querySelector("#id_section58_other"); // /PS-IGNORE

  // Field to modify
  const Sec58OtherDesc = document.querySelector("#id_other_description"); // /PS-IGNORE
  function clearOtherDescription() {
    Sec58OtherDesc.value = ""; // /PS-IGNORE
  }

  // Event handler
  section58Other.addEventListener("change", function (e) { // /PS-IGNORE
    showSec58OtherDesc(e.target.checked, {onHide: clearOtherDescription}); // /PS-IGNORE
  });
}
