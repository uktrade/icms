window.addEventListener('load', function (event) {
    const currentNotesLink = document.querySelector("#notes-current");
    const archivedNotesLink = document.querySelector("#notes-archived");

    const showCurrentNotes = UTILS.getShowElementFunc("#current-notes-list");
    const showArchivedNotes = UTILS.getShowElementFunc("#deleted-notes-list");

    currentNotesLink.addEventListener("click", function (event) {
        event.preventDefault();
        showCurrentNotes(true);
        showArchivedNotes(false);
        currentNotesLink.classList.add("current-tab");
        archivedNotesLink.classList.remove("current-tab");
    });

    archivedNotesLink.addEventListener("click", function (event) {
        event.preventDefault();
        if (parseInt(this.dataset.noteCount) === 0) {
            return;
        }

        showCurrentNotes(false);
        showArchivedNotes(true);
        archivedNotesLink.classList.add("current-tab");
        currentNotesLink.classList.remove("current-tab");
    });
});
