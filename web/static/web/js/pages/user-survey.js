window.addEventListener("DOMContentLoaded", function (event) {
  // Question: Did you experience any of the following issues?
  const otherCheckbox = document.querySelector("#id_issues_4");
  const noIssuesCheckbox = document.querySelector("#id_issues_5");
  const showOtherIssuesDetail = UTILS.getShowElementFunc("div.row_id_issue_details");
  showOtherIssuesDetail(otherCheckbox.checked === true);

  const otherTextArea = document.querySelector("#id_issue_details");
  otherTextArea.disabled = otherCheckbox.checked === false;

  otherCheckbox.addEventListener("change", function (e) {
    showOtherIssuesDetail(otherCheckbox.checked === true);
    otherTextArea.disabled = otherCheckbox.checked === false;
    if (otherCheckbox.checked === true) {
      noIssuesCheckbox.checked = false;
    } else {
      otherTextArea.value = "";
    }
  });

  for (let i = 0; i < 4; i++) {
    let checkbox = document.querySelector("#id_issues_" + i);
    checkbox.addEventListener("change", function (e) {
      if (checkbox.checked === true) {
        noIssuesCheckbox.checked = false;
      }
    });
  }

  noIssuesCheckbox.addEventListener("change", function (e) {
    if (noIssuesCheckbox.checked === true) {
      for (let i = 0; i < 5; i++) {
        let checkbox = document.querySelector("#id_issues_" + i);
        checkbox.checked = false;
      }
      showOtherIssuesDetail(false);
      otherTextArea.value = "";
    }
  });

  // Question: How was the process of finding the service?
  const findServiceSelect = document.querySelector("#id_find_service");
  const showFindServiceDetail = UTILS.getShowElementFunc("div.row_id_find_service_details");
  const serviceValues = ["DIFFICULT", "VERY_DIFFICULT"];
  showFindServiceDetail(serviceValues.includes(findServiceSelect.value));

  const findServiceDetailTextArea = document.querySelector("#id_find_service_details");
  findServiceDetailTextArea.disabled = !serviceValues.includes(findServiceSelect.value);

  findServiceSelect.addEventListener("change", function (e) {
    showFindServiceDetail(serviceValues.includes(findServiceSelect.value));
    findServiceDetailTextArea.disabled = !serviceValues.includes(findServiceSelect.value);
    if (findServiceDetailTextArea.disabled) {
      findServiceDetailTextArea.value = "";
    }
  });
});
