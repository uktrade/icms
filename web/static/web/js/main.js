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

        $('#remove-countries').click(function(){
            $('input.country_selector:checked').each(function(){
                $(this).closest('.country').remove();
            });
        });

        // Go to country group selected in dropdown list
        $('#country-group-select').change(function(){
            selected=$(this).val();
            window.location.href= '/country/groups/' + selected + '/';
        });

        $('#id_country_select_all').click(function(){
            $('.country_selector').each(function(){
                selector=$(this);
                selector.prop('checked', true);
            });
        });

        $('#id_country_select_none').click(function(){
            $('.country_selector').each(function(){
                selector=$(this);
                selector.prop('checked', false);
            });
        });

       function postOrdering(url) {
           ordering = $('.grabbable').sortable('toArray');
           csrftoken = document.cookie
              .split('; ')
              .find(function(e) {
                   return e.startsWith("csrf");
              }).split('=')[1];
           $.ajax({
               type: 'POST',
               url: url,
               data: {'order': ordering},
               headers: {
                  'X-CSRFToken': csrftoken,
                  'Content-Type': 'application/x-www-form-urlencoded'
               },
           });
       }

       $('.grabbable-group').sortable({
          opacity: 0.6,
          update: function(event, ui) {
             url = window.location.pathname + 'order/';
             postOrdering(url);
          }
        });

       $('.grabbable-calibre').sortable({
          opacity: 0.6,
          update: function(event, ui) {
               url = window.location.pathname.replace('edit', 'order');
               postOrdering(url);
          }
        });

        $('#calibre_display_archived_checkbox').change(function(e) {
            url = window.location.origin + window.location.pathname;
            if (e.target.checked) {
                url = url + '?display_archived=on';
            }
            window.location.href = url;
        });

        if(path=='/register/') {
            handle_security_question();
            $('#id_security_question_list').change(handle_security_question);
        }
        else if(path=='/import/apply/') {
          var post_form =function() {
            var form =$(this).closest('form');
            $('<input />')
              .attr('type','hidden')
              .attr('name', 'change')
              .attr('value', 'True')
              .appendTo(form);
            form.submit();
          };
          $('#id_application_type, #id_importer').change(post_form);
        }
        else if(path=='/export/create') {
            var post_form = function() {
              var form =$(this).closest('form');
              $('<input />')
                .attr('type','hidden')
                .attr('name', 'change')
                .attr('value', 'True')
                .appendTo(form);
              form.submit();
            };
            $('#id_application_type, #id_exporter').change(post_form);
        }

    }

    $(document).ready(initialise);

})(jQuery);

$(document).ready(function() {
    FOXjs.init(function() {});
});

function updateList() {
   var input = document.getElementById('id_files');
   var output = document.getElementById('fileList');
   var children = "";
   for (var i = 0; i < input.files.length; ++i) {
      children += '<li>' + input.files.item(i).name + '</li>';
   }
   output.innerHTML = '<ul>'+children+'</ul>';
}
