/*
Common code for import and export application search pages.
*/


function submitSearchForm(searchForm) {
  const inputs = searchForm.querySelectorAll("input, select");

  /* Disabling prevents empty values being submitted */
  inputs.forEach(
    function (input) {
      if (!input.value) {
        input.disabled = true;
      }
    }
  );

  searchForm.submit();
}

const setupSearchFormEventHandler = function () {
  const searchForm = document.querySelector("#search-application-form");

  searchForm.addEventListener("submit", function (e) {
    e.preventDefault();

    submitSearchForm(searchForm);
  });
}


const setupReassignFormEventHandler = function() {
  const reassignForm = document.querySelector("#reassign-to-form");
  const searchForm = document.querySelector("#search-application-form");
  const showReassignError = UTILS.getShowElementFunc("#reassign-failure-warning");

  // the reassign form doesn't always appear in the page.
  if (reassignForm === null) {
    return;
  }

  reassignForm.addEventListener("submit", function(e) {
    e.preventDefault();

    // form with "assign_to" and "applications" keys
    let formData = new FormData(reassignForm)

    // Search for all checked apps and
    const checkedApps = document.querySelectorAll('.application-checkbox_value:checked')
    checkedApps.forEach(
      function (checked) { formData.append("applications", checked.value) }
    );

    // reset error if needed:
    showReassignError(false);

    // ICMSLST-1182 Revisit if needed.
    fetch(
      reassignForm.action, {mode: 'same-origin', method: "POST", body: formData}
    )
      .then(function (response) {
        if (!response.ok) {
          showReassignError(true);
        } else {
          // resubmit the search form to update the results
          submitSearchForm(searchForm)
        }
      })
      .catch(function() { showReassignError(true) });
  });
}


const setupToggleCheckboxEventHandler = function (button, onClickChecked) {
  if (button === null) {
    return;
  }

  button.addEventListener('click', function(event) {
    const apps = document.querySelectorAll('.application-checkbox_value')

    apps.forEach(function(app) { app.checked = onClickChecked })
  });
}

/**
 * Submits the reopen case form and reloads the search page if successful.
 */
const setupReopenCaseFormHandlers = function () {
  const searchForm = document.querySelector("#search-application-form");
  const reopenCaseForms = document.querySelectorAll('form.reopen-case')
  const showReopenCaseWarning = UTILS.getShowElementFunc("#reopen-case-failure-warning")

  reopenCaseForms.forEach(function (reopenForm) {
    reopenForm.addEventListener("submit", function (e) {
      e.preventDefault();

      showReopenCaseWarning(false);

      const d = Dialogue();
      const message = "Are you sure you want to reopen this case?";
      const callback = function () {
        d.close();
        // CSRF token
        let formData = new FormData(reopenForm)
        fetch(
            reopenForm.action, {mode: 'same-origin', method: "POST", body: formData}
        )
            .then(function (response) {
              if (!response.ok) {
                showReopenCaseWarning(true);
              } else {
                // resubmit the search form to update the results
                submitSearchForm(searchForm);
              }
            })
            .catch(function () {
              showReopenCaseWarning(true)
            });
      }

      d.show(message, callback);
    });
  })
}
