(function($){

  $(document).ready(function() {
    $('.flash-message-close').click(function(){
      $(this).closest('.flash-message').remove();
    });
  });

})(jQuery)
