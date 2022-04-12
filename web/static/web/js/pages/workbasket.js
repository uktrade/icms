window.addEventListener('load', function (event) {
  const ajaxAnchorElements = document.querySelectorAll("a[data-is-ajax='1']");

  ajaxAnchorElements.forEach(
    function (node) {
      node.addEventListener("click", workbasketActionOnClickHandler);
    }
  );
});


function workbasketActionOnClickHandler(event) {
  event.preventDefault();
  // element: HTMLAnchorElement
  const element = event.target;

  const request = new Request(
    element.href,
    {mode: "same-origin", method: "GET"}
  );

  fetch(request)
    .then(function (response) {
      if (!response.ok) {
        showErrorDialogue()
      } else {
        response.json().then(
          function (data) {
            showResponseDialogue(data.msg, data.reload_workbasket)
          }
        )
      }
    })
    .catch(function () {
      showErrorDialogue();
    })
}


function showResponseDialogue(msg, reloadPage) {
  const d = Dialogue();

  const message = reloadPage ? `${msg} - Press OK to reload the workbasket` : msg;
  const callback = function () {
    reloadPage ? location.reload() : d.close()
  };

  d.show(message, callback);
}

function showErrorDialogue() {
  const message = "Unable to perform action - Press OK to reload the workbasket";
  const callback = function () {
    location.reload()
  }

  Dialogue().show(message, callback);
}
