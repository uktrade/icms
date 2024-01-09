window.addEventListener('load', function (event) {
    $('#remove-countries').click(function () {
        $('input.country_selector:checked').each(function () {
            $(this).closest('.country').remove();
        });
    });

    // Go to country group selected in dropdown list
    $('#country-group-select').change(function () {
        const countryId = encodeURIComponent($(this).val())
        window.location.href = `/country/groups/${countryId}/`
    });
});
