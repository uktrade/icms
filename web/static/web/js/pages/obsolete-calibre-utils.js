window.addEventListener('load', function (event) {
    $('.grabbable-group').sortable({
        opacity: 0.6,
        update: function (event, ui) {
            url = window.location.pathname + 'order/';
            postOrdering(url);
        }
    });

    $('.grabbable-calibre').sortable({
        opacity: 0.6,
        update: function (event, ui) {
            url = window.location.pathname.replace('edit', 'order');
            postOrdering(url);
        }
    });

    $('#calibre_display_archived_checkbox').change(function (e) {
        url = window.location.origin + window.location.pathname;
        if (e.target.checked) {
            url = url + '?display_archived=on';
        }
        window.location.href = url;
    });
});

function postOrdering(url) {
    ordering = $('.grabbable').sortable('toArray');
    csrftoken = document.cookie
        .split('; ')
        .find(function (e) {
            return e.startsWith("csrf");
        }).split('=')[1];
    $.ajax({
        type: 'POST',
        url: url,
        data: {'order': ordering},
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/x-www-form-urlencoded'
        },
    });
}
