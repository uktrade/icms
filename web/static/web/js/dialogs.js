var dialogs = (function($){

  var confirm = function(el, message) {

    confirmationDialog = 
      '<div class="modal-popover-container">' + 
        '<div class="modal-popover small-popover modal-alert-confirm">'+
          '<div class="modal-popover-content" role="alertdialog">'+
            '<div class="modal-popover-icon icon-question"></div>'+
            '<div class="modal-popover-text"></div>'+
              '<ul class="modal-popover-actions">'+
                '<li>' +
                  '<button class="primary-button alert-dismiss approve">OK</button>'+
                '</li>' +
                '<li>' + 
                  '<button class="link-button abort" >Cancel</button>' +
                '</li>' +
              '</ul>'+
          '</div>'+
        '</div>'+
      '</div>'

    el.click(function(e) {
      e.preventDefault();
      if ($('body').find('.modal-popover-container').length) {
        // Don't create modal is one already exist.
        return
      }
      var dialog = $(confirmationDialog).clone();
      dialog.find('.modal-popover-text').text(message)
      $('body').append(dialog)

      $(dialog).find('.abort').click(function(e){
        e.preventDefault();
        $(dialog).remove();
      });

      $(dialog).find('.approve').click(function(e){
        e.preventDefault();
        var form  = el.closest('form');
        console.log(form);
        var input=$("<input>")
          .attr("type", "hidden")
          .attr("name", el.attr('name'))
          .attr("value", el.attr('value'));
        form.append(input);
        form.submit();
      });
    });

  }

  $(document).ready(function() {
    $('[data-confirm]').each(function(){
      confirm($(this), $(this).attr('data-confirm'));
    });
  });

})(jQuery);
