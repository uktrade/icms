window.addEventListener('load', (event) => {
  setupDownloadSpreadsheetEventHandler({
    downloadId: "#download-search-spreadsheet",
    searchFormId: "#search-application-form",
    warningId: "#spreadsheet-download-warning"
  });
});
