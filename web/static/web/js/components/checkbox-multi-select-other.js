window.addEventListener("load", function (event) {
    const otherCheckbox = document.querySelector('input[type="checkbox"][value="Other"]');
    const showResponse = UTILS.getShowElementFunc("div.row_id_other_archive_reason");
    showResponse(otherCheckbox.checked === true);

    const otherTextArea = document.querySelector("#id_other_archive_reason");
    otherTextArea.disabled = otherCheckbox.checked === false;

    otherCheckbox.addEventListener("change", function (e) {
        showResponse(otherCheckbox.checked === true);
        otherTextArea.disabled = otherCheckbox.checked === false;
    });
});
