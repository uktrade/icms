window.addEventListener('load', (event) => {
  const appType = document.querySelector("#id_application_type");

  appType.addEventListener("change", (e) => {
    updateSubType();
  });
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
