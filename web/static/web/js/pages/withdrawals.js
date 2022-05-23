"use strict";

window.addEventListener("load", function (event) {
  const status = document.querySelector("#id_status");

  // The div row containing the response field
  const showResponse = UTILS.getShowElementFunc("div.row_id_response");
  showResponse(status.value === "rejected");

  status.addEventListener("change", function (e) {
    showResponse(e.target.value === "rejected");
  });
});
