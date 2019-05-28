(function($){

  function initialise() {
    // Address list is shown as links, clicking address saves the address and submits the form
    $('.link-save-address').click(function(){
      var address=$(this).text();
      $('#input-address').val(address);
      $('#form-save-address').submit();
      return false;
    });


    $('#id_country').change(function(){
      $('#form-manual-address').submit();
      return false;
    });
  }

  $(document).ready(initialise);

})(jQuery);
