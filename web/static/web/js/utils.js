/**
 * Global utility functions
 */

/**
 * Get a cookie (mainly used to get the csrf token)
 * https://docs.djangoproject.com/en/3.2/ref/csrf/#ajax
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


const UTILS = {
    /**
     * Returns a function that either shows or hides the element.
     *
     * Optional callbacks can be supplied when showing / hiding.
     * @param {string} elementSelector
     * @returns {(function(boolean, Object=): void)}
     */
    getShowElementFunc: function (elementSelector) {
        const element = document.querySelector(elementSelector);

        return (showElement = false, callbacks = {}) => {
            const {
                onShow = () => {},
                onHide = () => {}
            } = callbacks;

            if (showElement) {
                element.style.display = "block";
                onShow();
            } else {
                element.style.display = "none";
                onHide();
            }
        }
    }
}
