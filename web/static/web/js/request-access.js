"use strict";

document.addEventListener("DOMContentLoaded", function (event) { // doesn't work in IE8: https://caniuse.com/#feat=domcontentloaded
    var reasonRowClasses = getClasses('id_request_reason');
    var agentNameRowClasses = getClasses('id_agent_name');
    var agentAddressRowClasses = getClasses('id_agent_address');

    reasonRowClasses.add('hidden');
    agentNameRowClasses.add('hidden');
    agentAddressRowClasses.add('hidden');

    var container = document.getElementById('form-container');
    container.classList.remove('hidden');

    // which fields to show on the form based on the request type:
    var uiConfig = {
        'MAIN_IMPORTER_ACCESS': [1, 0, 0],
        'AGENT_IMPORTER_ACCESS': [1, 1, 1],
        'MAIN_EXPORTER_ACCESS': [0, 0, 0],
        'AGENT_EXPORTER_ACCESS': [0, 1, 1],
    };

    var dropdown = document.getElementById('id_request_type');
    dropdown.onchange = function () {
        showOrHide(uiConfig, dropdown, reasonRowClasses, agentNameRowClasses, agentAddressRowClasses);

        container.scrollIntoView(true);

        doRemoveOptionalLabels();
    };

    if (dropdown.value !== '') {
        // this is a POST request
        showOrHide(uiConfig, dropdown, reasonRowClasses, agentNameRowClasses, agentAddressRowClasses);
        doRemoveOptionalLabels();
        container.scrollIntoView(true);
    }
});

function showOrHide(uiConfig, dropdown, reasonRowClasses, agentNameRowClasses, agentAddressRowClasses) {
    if (dropdown.options.length === 5) {
        dropdown.remove(0);
    }

    uiConfig[dropdown.value][0] ? reasonRowClasses.remove('hidden') : reasonRowClasses.add('hidden');
    uiConfig[dropdown.value][1] ? agentNameRowClasses.remove('hidden') : agentNameRowClasses.add('hidden');
    uiConfig[dropdown.value][2] ? agentAddressRowClasses.remove('hidden') : agentAddressRowClasses.add('hidden');
}

function getClasses(id) {
    return document.getElementById(id).parentElement.parentElement.classList;
}

function doRemoveOptionalLabels() {
    removeOptionalLabels();
    removeOptionalLabels(); // needs two calls, for some unknown reason, to fully do the job ...
}

function removeOptionalLabels() {
    var optionalTags = document.getElementsByClassName("mand-label");
    for (var i = 0; i < optionalTags.length; i++) {
        optionalTags[i].parentNode.removeChild(optionalTags[i]);
    }
}

