window.addEventListener('load', function (event) {
    $('#id_country_select_all').click(function () {
        $('.country_selector').each(function () {
            let selector = $(this);
            selector.prop('checked', true);
        });
    });

    $('#id_country_select_none').click(function () {
        $('.country_selector').each(function () {
            let selector = $(this);
            selector.prop('checked', false);
        });
    });
});
