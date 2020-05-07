$(document).ready(function() {
    $('[role=action-button]').off().on('click', function(evt){

        evt.preventDefault();
        var $el = $(this)
        var url    = $el.attr('href');
        var action = $el.attr('data-action');
        var csrf   = $el.attr('data-csrf');
        var method = $el.attr('data-method') || 'POST';
        var item   = $el.attr('data-item');
        // TODO: Move link action outside the table, link selected
        var viewflow_started = $el.next('input[name=_viewflow_activation-started]').attr('value')

        var standAloneAction = function(){
            console.log('running standAloneAction callback')
            $frm = $('<form></form>');
            $frm.attr('method', method);

            if (url) {
                $frm.attr('action', url);
            }

            if (csrf) {
                $frm.append('<input type="hidden" name="csrfmiddlewaretoken" value="'+ csrf +'"/>')
            }

            if (item) {
                $frm.append('<input type="hidden" name="item" value="'+ item +'" />')
            }

            if (viewflow_started) {
                $frm.append('<input type="hidden" name="_viewflow_activation-started" value="'+ viewflow_started +'" />')
                $frm.append('<input type="hidden" name="_continue"'+ '/>')
            }

            $frm.append('<input type="hidden" name="action" value="'+ action +'" />')

            $('body').append($frm);
            $frm.submit();
        };

        var inFormAction = function() {
            console.log('running inFormAction callback')

            $frm = $el.closest('frm');
            $frm.append('<input type="hidden" name="action" value="'+ action +'" />')
            $frm.submit();
        }

        var callback = $el.is('[data-in-form]') ? inFormAction : standAloneAction;

        var confirmMessage =  $el.attr('data-confirm');
        if (confirmMessage) {
            return Dialogue().show(confirmMessage, callback);
        }

        callback();
    });
});




