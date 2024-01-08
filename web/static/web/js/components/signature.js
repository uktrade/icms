function signatureUploadOnInput(e) {
  window.fileUrl !== null && window.fileUrl.revokeObjectURL();
  window.fileUrl = window.URL.createObjectURL(e.srcElement.files[0]);
  document.querySelector("#signature-widget-image").src = window.fileUrl;
  document.querySelector("#signature-widget-row").hidden = false;
}

function signatoryTextChange(e) {
  document.querySelector("#signature-widget-signatory").textContent = e.srcElement.value;
}

window.addEventListener('load', function (event) {
  this.window.fileUrl = null;
  document.querySelector("#id_file").oninput = signatureUploadOnInput;
  let signatoryInput = document.querySelector("#id_signatory");
  document.querySelector("#signature-widget-signatory").textContent = signatoryInput.value;
  signatoryInput.addEventListener("change", signatoryTextChange);
});
