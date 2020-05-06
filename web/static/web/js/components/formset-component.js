$(document).ready(function(){
    $('[role=formset]').each(function(index, el){
        var $el = $(el);
        var prefix = $el.attr('data-formset-prefix');
        var addText = $el.attr('data-formset-add-text') || 'Add';
        var removeText = $el.attr('data-formset-remove-text') || 'Remove';
        var formCssClass = $el.attr('data-formset-form-css-class') || prefix + '-form';
        var addCssClass = $el.attr('data-formset-add-css-class') || 'icon-phone small-button button';

        $el.find('tbody tr').formset({
            prefix: prefix,
            formCssClass: formCssClass,
            addCssClass: addCssClass ,
            addText: addText,
            deleteText: removeText,
        });
    });
});