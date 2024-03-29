// This is only used for a very small subset of views that inherit from PostActionMixin
// Removed most references to it as it was causing exceptions.
$(document).ready(function() {
    $('[role=action-button]').off().on('click', function(evt){

        evt.preventDefault();
      
        var $el = $(this)
        var button_name = $el.attr('name') // Clicked button name attribute
        var button_value = $el.attr('value') // Clicked button value attribute
        var url    = $el.attr('href');
        var data = $el.data()
        var method = data['method'] || 'POST'
        var confirmMessage =  data['confirm']
        var form = $el.closest('form')

        var submit = function(){
            console.log('running form submit')
            if(form.length) { // If there is wrapping form use it
              $frm = form
              console.log('Using existing form')
            } else {
              $frm = $('<form></form>');
              $('body').append($frm);
              $frm.attr('method', method);
              if (url) {
                $frm.attr('action', url);
              }
            }

            if(button_name) {
              $frm.append('<input type="hidden" name="' + button_name + '" value="' + button_value + '" />')
            }

            // Add data attributes as hidden inputs
            for (var key in data) {
              if (key.substring(0,6) == 'input_'){
                var name = key.substring(6)
                console.log(name)
                $frm.append('<input type="hidden" name="' + name + '" value="' + data[key] + '" />')
              }
            }

            $frm.submit();
        };

        if (confirmMessage) {
            return Dialogue().show(confirmMessage, submit);
        } 

        submit();
    });
});
