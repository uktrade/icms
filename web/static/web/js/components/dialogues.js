// A simple dialogue component that can be used to show a confirmation dialogue, OK and cancel buttons
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
        formSubmitted: false,
        bindTo: function (el, message) {
            let that = this;
            el.on('click', function (evt) {
                evt.preventDefault();
                that.show(message, function () {
                    var form = el.closest('form');
                    var input = $("<input>")
                      .attr("type", "hidden")
                      .attr("name", el.attr('name'))
                      .attr("value", el.attr('value'));
                    form.append(input);

                    // Prevent double submission of the form.
                    if (!that.formSubmitted) {
                        that.formSubmitted = true;
                        form.submit();
                    }
                });
            });
        },

        close: function() {
            this.d.remove();
        }
    };
};

// A simple dialogue component that can be used to show a message with an OK button
const ModalMessage = function () {
    const modalMessage =
        '<div class="modal-popover-container">' +
        '<div class="modal-popover small-popover modal-alert-confirm">'+
            '<div class="modal-popover-content" role="alertdialog">'+
            '<div class="modal-popover-icon icon-question"></div>'+
            '<div class="modal-popover-text"></div>'+
                '<ul class="modal-popover-actions">'+
                '<li>' +
                    '<button class="primary-button alert-dismiss">OK</button>'+
                '</li>' +
                '</ul>'+
            '</div>'+
        '</div>'+
        '</div>'

    return {
        d: $(modalMessage).clone(),
        show: function (message, successCallback) {
            const $body = $('body');

            if ($body.find('.modal-popover-container:visible').length) {
                // Don't create modal if one already exist.
                console.error('Another dialogue is visible, not showing this one');
                return;
            }

            this.d.find('.modal-popover-text').html(message);
            $body.append(this.d);

            this.d.find('.alert-dismiss').click(
              (e) => {
                  e.preventDefault();
                  this.close();
              });
        },

        bindTo: function (el, message) {
            let that = this;
            el.on('click', function (evt) {
                evt.preventDefault();
                that.show(message);
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
    $('[data-modal-message]').each(function(){
        ModalMessage().bindTo($(this), $(this).attr('data-modal-message'));
    });
});
