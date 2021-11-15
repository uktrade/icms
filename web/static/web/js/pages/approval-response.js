document.addEventListener("DOMContentLoaded", function (event) { // doesn't work in IE8: https://caniuse.com/#feat=domcontentloaded
    "use strict";

    const showRefuseReason = UTILS.getShowElementFunc(".row_id_refuse_reason");
    const decision = document.querySelector('#id_decision');

    // Set initial value
    showRefuseReason(decision.value === "REFUSE");

    decision.addEventListener("change", function (e) {
        const choice = e.target.value;

        showRefuseReason(
          choice === "REFUSE", {
              onHide: () => document.querySelector("#id_refuse_reason").value = null
            }
        );
    });
});
