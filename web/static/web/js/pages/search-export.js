window.addEventListener('load', function (event) {
  const reassignmentCB = document.querySelector("#id_reassignment");
  // The reassignment checkbox doesn't always appear on the page.
  if (reassignmentCB !== null) {
    const showReassignUser = UTILS.getShowElementFunc("#reassignment-user-wrapper");

    reassignmentCB.addEventListener("change", (e) => {
      showReassignUser(e.target.checked, {
        onHide: () => $("#id_reassignment_user").djangoSelect2().empty()
      });
    });
  }

  setupDownloadSpreadsheetEventHandler({
    downloadId: "#download-search-spreadsheet",
    searchFormId: "#search-application-form",
    warningId: "#spreadsheet-download-warning"
  });

  /* strips empty search values */
  setupSearchFormEventHandler();

  /* Reassignment handlers */
  setupReassignFormEventHandler();
  const selectAllBtn = document.querySelector("#select-all-records");
  setupToggleCheckboxEventHandler(selectAllBtn, true)
  const unselectAllBtn = document.querySelector("#unselect-all-records")
  setupToggleCheckboxEventHandler(unselectAllBtn, false)

  /* Results table row actions */
  setupReopenCaseFormHandlers();
});
