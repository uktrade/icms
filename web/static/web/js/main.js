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


    function on_add_new_calibre(row) {
        adjust_sort_arrows(row);
        adjust_sort_arrows(row.prev());
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
                console.log('hello');
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
            prefix: 'calibres',
            formCssClass: 'calibres-form',
            addCssClass: 'small-button icon-plus button',
            addText: 'Add Obsoloete Calibre',
            deleteText: '',
            added: on_add_new_calibre
        });

        $('button[name="calibre-move-up"]').click(function() {
            row = $(this).closest('tr');
            previous = row.prev('tr');
            if(previous.length) {
                previous.before(row);
                adjust_sort_arrows(row);
                adjust_sort_arrows(previous);
            }
        });

        $('button[name="calibre-move-down"]').click(function() {
            row = $(this).closest('tr');
            next = row.next('tr');
            if(next.length){
                next.after(row);
                adjust_sort_arrows(row);
                adjust_sort_arrows(next);
            }
        });

        if(path=='/register/') {
            handle_security_question();
            $('#id_security_question_list').change(handle_security_question);
        }
    }

    $(document).ready(initialise);

})(jQuery);
