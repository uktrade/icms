$(document).ready(function() {
    $('[role=action-button]').off().on('click', function(evt){

        evt.preventDefault();
        var $el = $(this)
        var url    = $el.attr('href');
        var action = $el.attr('data-action');
        var csrf   = $el.attr('data-csrf');
        var method = $el.attr('data-method') || 'POST';
        var item   = $el.attr('data-item');
        var form = $el.closest('form')

        var submit = function(){
            console.log('running form submit')
            if(form.length) { // If there is wrapping form use it
              $frm = form
              console.log('Using existing form')
            } else {
              $frm = $('<form></form>');
              $('body').append($frm);
            }
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

            $frm.append('<input type="hidden" name="action" value="'+ action +'" />')

            $frm.submit();
        };

        var confirmMessage =  $el.attr('data-confirm');
        if (confirmMessage) {
            return Dialogue().show(confirmMessage, submit);
        }

        submit();
    });
});




