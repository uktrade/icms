"use strict";

window.addEventListener('load', (event) => {
  // Holds information about the initial state of forms.
  let formState = {};

  // Only check forms that have opted in for preventing form data loss
  const watchedForms = document.querySelectorAll("form[class=prevent-data-loss]")

  watchedForms.forEach((form, index) => {
      // True when the form was loaded with errors
      const hadErrors = form.querySelectorAll("div.error-message").length > 0;

      if (hadErrors) {
        // Assume no data has been saved if the form was loaded with errors.
        formState[index] = new Set()
      } else {
        const formData = new FormData(form);
        formState[index] = convertToSet(formData);
      }
    }
  )

  // https://developer.mozilla.org/en-US/docs/web/api/window/beforeunload_event#examples
  // https://html.spec.whatwg.org/multipage/browsing-the-web.html#unloading-documents
  window.addEventListener('beforeunload', (event) => {
    // Check if we are submitting a form
    const activeForm = document.activeElement.closest("form");

    if (formStateChanged(watchedForms, formState, activeForm)) {
      event.preventDefault();
      return event.returnValue = "";
    }
  });
});


/**
 * Check if form state has changed
 * @param {NodeList} watchedForms The forms being checked for data loss
 * @param initialState Initial from state
 * @param activeForm form we are submitting.
 * @returns {boolean} True when there is unsaved form state.
 */
function formStateChanged(watchedForms, initialState, activeForm) {
  return Array.from(watchedForms).some(
    (form, index) => {
      if (form !== activeForm) {
        const initial = initialState[index]
        const newState = convertToSet(new FormData(form))

        if (!setsAreEqual(initial, newState)) {
          return true;
        }
      }
    });
}


/**
 * Convert a FormData instance into a set of unique values
 * @param {FormData} formData
 * @returns {Set<any>}
 */
function convertToSet(formData) {
  const setData = new Set()

  for (let [key, value] of formData) {
    setData.add(`${key}-${value}`)
  }

  return setData
}


// Link to check if two sets are equal:
// https://bobbyhadz.com/blog/javascript-check-if-two-sets-are-equal
function setsAreEqual(a, b) {
  if (a.size !== b.size) {
    return false;
  }

  return Array.from(a).every(element => {
    return b.has(element);
  });
}
