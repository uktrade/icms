(function($){

  function handle_security_question(){
    var selected=$('#id_security_question_list').val();
    var question=$('#id_security_question');
    var row = question.closest('div[class="row"]');
    if(selected=='' || selected !='OWN_QUESTION') {
      row.hide();
    } else {
      row.show();
    }
  }


  function initialise() {

    var path= window.location.pathname;

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

    if(path=='/register/') {
      handle_security_question();
      $('#id_security_question_list').change(handle_security_question);
    }
  }

  $(document).ready(initialise);

})(jQuery);
