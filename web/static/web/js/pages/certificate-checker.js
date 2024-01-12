function toggleHelper(e) {
    const parent = e.srcElement.parentElement.parentElement
    const arrow = parent.getElementsByClassName("arrow")[0];
    const panel = parent.getElementsByClassName("helper-panel")[0];

    "none" == panel.style.display ? (
        panel.style.display = "block",
        arrow.innerHTML = "▼") : (
        panel.style.display = "none",
        arrow.innerHTML = "►"
    )
}

window.addEventListener('load', (event) => {
    const whereToFindElements = document.querySelectorAll(".whereToFind");
    whereToFindElements.forEach((el) => el.addEventListener("click", toggleHelper));
});
