window.addEventListener('load', (event) => {
  const reassignmentCB = document.querySelector("#id_reassignment");
  const showReassignUser = UTILS.getShowElementFunc("#reassignment-user-wrapper")

  reassignmentCB.addEventListener("change", (e) => {
    showReassignUser(e.target.checked, {
      onHide: () => $("#id_reassignment_user").djangoSelect2().empty()
    });
  });

  setupDownloadSpreadsheetEventHandler({
    downloadId: "#download-search-spreadsheet",
    searchFormId: "#search-application-form",
    warningId: "#spreadsheet-download-warning"
  });
});
