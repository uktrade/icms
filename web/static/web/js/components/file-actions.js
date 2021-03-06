$(document).ready(function(){
    $('[role=file-upload]').on('click', function(evt){
        evt.preventDefault();
        $el = $(evt.currentTarget);
        $frm = $el.closest('form');
        $input = $frm.find('input[type=file]').first();

        // prevent binding the same code to change event multiple times
        $input.off('change')

        $input.on('change', function(evt){
            var filename = evt.target.files[0].name;
            $template = $($($el.attr('x-file-upload-template')).html());

            $template.find('[role=filename]').html(filename);
            $template.find('[role=filename]').attr('href', 'javascript:;');
            $template.find('[role=actions]').html('<a href="javascript:;" class="fileInfo readonly" style="white-space: nowrap;"><span class="icon-animated-spinner"></span> uploading ...</a>');
            $template.find('[role=username]').html('');
            $template.find('[role=date]').html('');
            $template.find('[role=filesize]').html('');
            $template.removeClass('deleted-file')

            $frm.find('[role=file-list] tbody').prepend($template);

            $frm.append('<input type="hidden" name="_upload"/>');
            $frm.attr('enctype', "multipart/form-data");

            $frm.submit();
        });

        $input.click();
    });


    $('[role=file-delete]').on('click', function(evt){
        evt.preventDefault();
        $el = $(evt.currentTarget);
        $frm = $el.closest('form');
        $frm.append('<input type="hidden" name="_delete" />');
        $frm.append('<input type="hidden" name="_file_id" value="'+ $el.attr('x-file-id') +'"/>');
        $frm.submit();
    });


    $('[role=file-restore]').on('click', function(evt){
        evt.preventDefault();
        $el = $(evt.currentTarget);
        $frm = $el.closest('form');
        $frm.append('<input type="hidden" name="_restore" />');
        $frm.append('<input type="hidden" name="_file_id" value="'+ $el.attr('x-file-id') +'"/>');
        $frm.submit();
    });


    $('[role=deleted-files-control]').on('click', function(evt){
        evt.stopPropagation();
        $el = $(evt.currentTarget);
        $tbl = $('[role=file-list]').first();
        $tbl.toggleClass('show-deleted')
    });
});
