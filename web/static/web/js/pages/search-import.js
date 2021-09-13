window.addEventListener('load', (event) => {
  const appType = document.querySelector("#id_application_type");

  appType.addEventListener("change", (e) => {
    updateSubType();
  });

  // downloadForm isn't always in the dom so check it exists.
  const downloadForm = document.querySelector("#download-search-spreadsheet")
  if (downloadForm !== null) {
    downloadForm.addEventListener("click", (e) => {
      e.preventDefault();
      const warning = document.querySelector("#spreadsheet-download-warning");

      handleResultsSpreadsheetDownload(downloadForm)
        .then(() => {
          warning.style.display = "none";
        })
        .catch(reason => {
          warning.style.display = "block";
          console.log(reason);
        });
    });
  }
});

function updateSubType() {
  const appType = document.querySelector("#id_application_type");
  const appSubType = document.querySelector("#id_application_sub_type");
  const appSubTypeWrapper = document.querySelector("#application-sub-type-wrapper");

  if (appType.value === "FA") {
    appSubTypeWrapper.style.display = "block";
  } else {
    appSubType.value = "";
    appSubTypeWrapper.style.display = "none";
  }
}

async function handleResultsSpreadsheetDownload(downloadForm) {
  const downloadUrl = downloadForm.action;

  // Copy the search form data
  const searchForm = document.querySelector('#search-application-form');
  const formData = new FormData(searchForm)

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
  link.download = `import_application_download_${stamp}`;

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
