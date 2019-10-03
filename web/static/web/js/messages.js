(function($){

  $(document).ready(function() {
    $('.flash-message-close').click(function(){
      console.log($(this));
      $(this).closest('.flash-message').remove();
    });
  });

})(jQuery)
