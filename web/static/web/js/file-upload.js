$(document).ready(function(){
    $('[role=file-upload]').on('click', function(evt){
        evt.preventDefault();
        $el = $(evt.currentTarget)
        $frm = $el.closest('form');
        $input = $frm.find('input[type=file]').first();

        // prevent binding the same code to change event multiple times
        $input.off('change')

        $input.on('change', function(evt){
            var filename = evt.target.files[0].name
            $template = $($($el.attr('x-file-upload-template')).html())

            $template.find('[role=filename]').html(filename)
            $template.find('[role=filename]').attr('href', 'javascript:;')
            $template.find('[role=actions]').html('<a href="javascript:;" class="fileInfo readonly"><span class="icon-animated-spinner"></span> uploading ...</a>')
            $template.find('[role=username]').html('')
            $template.find('[role=date]').html('')
            $template.find('[role=filesize]').html('')

            $frm.find('[role=file-list] tbody').prepend($template)
        });

    $input.click();
    });
})