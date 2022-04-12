const Dialogue = function () {
    const confirmationDialog =
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
        d: $(confirmationDialog).clone(),
        show: function (message, successCallback) {
            const $body = $('body');

            if ($body.find('.modal-popover-container:visible').length) {
                // Don't create modal if one already exist.
                console.error('Another dialogue is visible, not showing this one');
                return;
            }

            this.d.find('.modal-popover-text').html(message);
            $body.append(this.d);

            this.d.find('.abort').click(
              (e) => {
                  e.preventDefault();
                  this.close();
              });

            this.d.find('.approve').click(
              (e) => {
                  e.preventDefault();
                  if (successCallback) {
                      return successCallback();
                  }
              });
        },

        bindTo: function (el, message) {
            let that = this;

            el.on('click', function (evt) {
                evt.preventDefault();
                that.show(message, function () {
                    var form = el.closest('form');
                    console.log('running default callback');
                    var input = $("<input>")
                      .attr("type", "hidden")
                      .attr("name", el.attr('name'))
                      .attr("value", el.attr('value'));
                    form.append(input);
                    form.submit();
                });
            });
        },

        close: function() {
            this.d.remove();
        }
    };
};

$(document).ready(function() {
    $('[data-confirm]').each(function(){
        Dialogue().bindTo($(this), $(this).attr('data-confirm'));
    });
});
