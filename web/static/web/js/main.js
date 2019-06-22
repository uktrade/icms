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


    $('#id_select_all').click(function(){
        $('.item_selector').each(function(){
            selector=$(this);
            selector.prop('checked', true);
        });
    });

    $('#id_select_none').click(function(){
          $('.item_selector').each(function(){
              selector=$(this);
              selector.prop('checked', false);
          });
     });

     $('.icon-user-minus').click(function(){
         $(this).closest('tr').remove();
     });

      $('.add-person').click(function(e){
          console.log('Adding input');
          role_id=$(this).attr('data-role');
          $(this).append(
              '<input type="hidden" name="add_to_role" value="'
                  + role_id
                  + '" />'
          );
      });





    if(path=='/register/') {
      handle_security_question();
      $('#id_security_question_list').change(handle_security_question);
    }
  }

  $(document).ready(initialise);

})(jQuery);
