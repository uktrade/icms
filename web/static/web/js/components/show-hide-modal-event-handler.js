var hide_modal_buttons = document.getElementsByClassName("hide-modal-button");
var show_modal_buttons = document.getElementsByClassName("show-modal-button");

var hideModal = function () {
    $('.modal-popover-container').hide();
};

var showModal = function () {
    $('.modal-popover-container').show();
};

for (var i = 0; i < hide_modal_buttons.length; i++) {
    hide_modal_buttons[i].addEventListener('click', hideModal, false);
}

for (var i = 0; i < show_modal_buttons.length; i++) {
    show_modal_buttons[i].addEventListener('click', showModal, false);
}
