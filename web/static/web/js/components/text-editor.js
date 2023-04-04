if ($('textarea').length) {
    const readonly = document.currentScript.getAttribute("readonly") === "true";

    let buttons = [];

    if (readonly === false) {
        buttons = [
            'bold',
            'underline',
            'italic',
            'align',
        ]
    }

    Jodit.make('textarea', {
        readonly: readonly,
        buttons: buttons,
        buttonsMD: buttons,
        buttonsSM: buttons,
        buttonsXS: buttons,
        toolbar: !readonly,
        height: document.currentScript.getAttribute("height"),
        showCharsCounter: false,
        showWordsCounter: false,
        showXPathInStatusbar: false,
    });
}
