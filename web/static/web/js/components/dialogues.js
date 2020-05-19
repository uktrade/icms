var Dialogue = function () {
    confirmationDialog =
        '<div class="modal-popover-container">' +
        '<div class="modal-popover small-popover modal-alert-confirm">'+
            '<div class="modal-popover-content" role="alertdialog">'+
            '<div class="modal-popover-icon icon-question"></div>'+
            '<div class="modal-popover-text"></div>'+
                '<ul class="modal-popover-actions">'+
                '<li>' +
                    '<button class="primary-button alert-dismiss approve">OK</button>'+
                '</li>' +
                '<li>' +
                    '<button class="link-button abort" >Cancel</button>' +
                '</li>' +
                '</ul>'+
            '</div>'+
        '</div>'+
        '</div>'

    return {
        show : function(message, successCallback){
            if ($('body').find('.modal-popover-container:visible').length) {
                // Don't create modal if one already exist.
                console.log('Another dialogue is visible, not showing this one');
                return;
            }

            var dialog = $(confirmationDialog).clone();
            dialog.find('.modal-popover-text').html(message);
            $('body').append(dialog);

            $(dialog).find('.abort').click(function(e){
                e.preventDefault();
                $(dialog).remove();
            });

            $(dialog).find('.approve').click(function(e){
                e.preventDefault();
                if (successCallback) {
                    return successCallback();
                }
            });
        },

        bindTo: function(el, message){
            var that = this;
            el.on('click', function(evt){
                evt.preventDefault();
                that.show(message, function(){
                    var form  = el.closest('form');
                    console.log('running default callback');
                    var input=$("<input>")
                        .attr("type",  "hidden")
                        .attr("name",  el.attr('name'))
                        .attr("value", el.attr('value'));
                    form.append(input);
                    form.submit();
                });
            });
        }
    };
};

$(document).ready(function() {
    $('[data-confirm]').each(function(){
        Dialogue().bindTo($(this), $(this).attr('data-confirm'));
    });
});
