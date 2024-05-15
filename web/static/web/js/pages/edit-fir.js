document.addEventListener("DOMContentLoaded", function (event) {
    document.getElementById('save-fir-request-button').addEventListener("click", function (event) {
        document.querySelector('input[name=send]').value = "False";
        document.getElementById('edit-fir-form').submit();
    });

    document.getElementById('send-fir-request-button').addEventListener("click", function (event) {
        document.getElementById('manage-ownership-modal').classList.remove('hidden');
        document.querySelector('input[name=send]').value = "True";
    });

    document.getElementById('release-ownership-button').addEventListener("click", function (event) {
        document.getElementById('manage-ownership-modal').classList.add('hidden');
        document.querySelector('input[name=release_ownership]').value = 'True';
        document.getElementById('edit-fir-form').submit();
    });

    document.getElementById('retain-ownership-button').addEventListener("click", function (event) {
        document.getElementById('manage-ownership-modal').classList.add('hidden');
        document.querySelector('input[name=release_ownership]').value = 'False';
        document.getElementById('edit-fir-form').submit();
    });
});
