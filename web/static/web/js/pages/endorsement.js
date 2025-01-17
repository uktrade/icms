window.addEventListener('DOMContentLoaded', (event) => {
    const endorsementSelect = document.querySelector("#id_content");

    endorsementSelect.addEventListener("change", function (e) {
        endorsementTextLookup(e.target.value).then((response) => {
            if (response.ok) {
                response.json().then(data => {
                    document.querySelector("#endorsement-text").innerHTML = data.text;
                })
            } else {
                document.querySelector("#endorsement-text").innerHTML = "";
            }
        });
    });
});

