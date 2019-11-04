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

    function adjust_sort_arrows(row){
        if(row.prev('tr').length){
            row.find('.move-up').show();
        } else {
            row.find('.move-up').hide();
        }

        if(row.next('tr').length) {
            row.find('.move-down').show();
        } else {
            row.find('.move-down').hide();
        }
    }


    function swap_orders(row1, row2) {
        row1_order_input = row1.find('.calibre-order input');
        row2_order_input = row2.find('.calibre-order input');
        row1_order = row1_order_input.val();
        row2_order = row2_order_input.val();
        console.log(row1_order);
        console.log(row2_order);
        row1_order_input.val(row2_order);
        row2_order_input.val(row1_order);
    }

    function move_down() {
        row = $(this).closest('tr');
        next = row.next('tr');
        if(next.length){
            next.after(row);
            swap_orders(row, next);
            adjust_sort_arrows(row);
            adjust_sort_arrows(next);
        }
    }


    function move_up() {
        row = $(this).closest('tr');
        previous = row.prev('tr');
        if(previous.length) {
            previous.before(row);
            swap_orders(row, previous);
            adjust_sort_arrows(row);
            adjust_sort_arrows(previous);
        }
    }

    function on_add_new_calibre(row) {
        previous=row.prev();
        last_order = previous.find('.calibre-order input').val();
        row.find('.calibre-status').text('Pending');
        row.find('.calibre-order input').val(+last_order+1);
        adjust_sort_arrows(row);
        adjust_sort_arrows(previous);
        row.find('button[name="calibre-move-down"]').click(move_down);
        row.find('button[name="calibre-move-up"]').click(move_up);
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


        $('#obsolete-calibres-table tbody tr').formset({
            prefix: 'calibre',
            formCssClass: 'calibres-form',
            addCssClass: 'small-button icon-plus button',
            addText: 'Add Obsolete Calibre',
            deleteText: '',
            added: on_add_new_calibre
        });

        $('#calibre_display_archived_checkbox').change(function(e) {
            url = window.location.origin + window.location.pathname;
            if (e.target.checked) {
                url = url + '?display_archived=on';
            }
            window.location.href = url;
        });

        $('button[name="calibre-move-up"]').click(move_up);
        $('button[name="calibre-move-down"]').click(move_down);

        if(path=='/register/') {
            handle_security_question();
            $('#id_security_question_list').change(handle_security_question);
        }

        if(path=='/import/apply/') {
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
    }

    $(document).ready(initialise);

})(jQuery);
