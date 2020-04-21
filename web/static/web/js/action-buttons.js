$(document).ready(function() {
    $('[role=action-button]').off().on('click', function(evt){

        evt.preventDefault();
        var url    = $(this).attr('href');
        var action = $(this).attr('data-action');
        var csrf   = $(this).attr('data-csrf');
        var method = $(this).attr('data-method') || 'POST';

        var confirmMessage =  $(this).attr('data-confirm');

        var doAction = function(){
            console.log('running action button callback')
            $frm = $('<form></form>');
            $frm.attr('method', method);

            if (url) {
                $frm.attr('action', url);
            }

            if (csrf) {
                $frm.append('<input type="hidden" name="csrfmiddlewaretoken" value="'+ csrf +'"/>')
            }

            $frm.append('<input type="hidden" name="action" value="'+ action +'" />')

            $('body').append($frm);
            $frm.submit();
        };

        if (confirmMessage) {
            return Dialogue().show(confirmMessage, doAction);
        }

        doAction();
    });
});




