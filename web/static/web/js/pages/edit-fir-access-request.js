document.addEventListener("DOMContentLoaded", function (event) {
    document.getElementById('save-fir-request-button').addEventListener("click", function (event) {
        document.querySelector('input[name=send]').value = "False";
        document.getElementById('edit-fir-form').submit();
    });

    document.getElementById('send-fir-request-button').addEventListener("click", function (event) {
        document.querySelector('input[name=send]').value = "True";
        document.getElementById('edit-fir-form').submit();
    });
});
