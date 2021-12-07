
function setupDownloadSpreadsheetEventHandler({ downloadId, searchFormId, warningId }) {
  const downloadForm = document.querySelector(downloadId)

  if (downloadForm !== null) {
    downloadForm.addEventListener("click", (e) => {
      e.preventDefault();
      const warning = document.querySelector(warningId);

      handleResultsSpreadsheetDownload(downloadForm, searchFormId)
        .then(() => {
          warning.style.display = "none";
        })
        .catch(reason => {
          warning.style.display = "block";
          console.warn(reason);
        });
    });
  }
}


/**
 * Download an application results spreadsheet.
 * @param {string} downloadForm
 * @param {string} searchFormId
 */
async function handleResultsSpreadsheetDownload(downloadForm, searchFormId) {
  const downloadUrl = downloadForm.action;

  // Copy the search form data
  const searchForm = document.querySelector(searchFormId);
  let formData = new FormData(searchForm)
  formData.append("csrfmiddlewaretoken", downloadForm.csrfmiddlewaretoken.value)

  const response = await fetch(downloadUrl, {mode: 'same-origin', method: "POST", body: formData})

  if (!response.ok) {
    return Promise.reject("Unable to download spreadsheet");
  }

  // Download the spreadsheet
  const spreadsheetFile = await response.blob();
  downloadFile(spreadsheetFile)
}


/**
 * Create a link and simulate a click event to download the supplied file object.
 */
function downloadFile(file) {
  // Create a link and set the URL using `createObjectURL`
  const link = document.createElement("a");
  link.style.display = "none";
  link.href = URL.createObjectURL(file);
  const stamp = fileTimestamp();
  link.download = `search_application_download_${stamp}`;

  // It needs to be added to the DOM so it can be clicked
  document.body.appendChild(link);
  link.click();

  // To make this work on Firefox we need to wait
  // a little while before removing it.
  setTimeout(() => {
    URL.revokeObjectURL(link.href);
    link.parentNode.removeChild(link);
  }, 0);
}


function fileTimestamp() {
  let today = new Date();
  let tDate = today.toLocaleDateString();
  let tTime = today.toLocaleTimeString();

  return `${tDate}_${tTime}`;
}
