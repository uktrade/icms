document.addEventListener("DOMContentLoaded", function(event) { // doesn't work in IE8: https://caniuse.com/#feat=domcontentloaded
    'use strict';
    var reasonRowClasses = getClasses('id_request_reason');
    var agentNameRowClasses = getClasses('id_agent_name');
    var agentAddressRowClasses = getClasses('id_agent_address');

    reasonRowClasses.add('hidden');
    agentNameRowClasses.add('hidden');
    agentAddressRowClasses.add('hidden');

    var container = document.getElementById('form-container');
    container.classList.remove('hidden');

    var dropdown = document.getElementById('id_request_type');
    dropdown.onchange = function () {
        if (dropdown.options.length > 4) {
            dropdown.remove(0);
        }
        switch (dropdown.value) {
            case 'MAIN_IMPORTER_ACCESS':
                reasonRowClasses.remove('hidden');
                agentNameRowClasses.add('hidden');
                agentAddressRowClasses.add('hidden');
                break;
            case 'AGENT_IMPORTER_ACCESS':
                reasonRowClasses.remove('hidden');
                agentNameRowClasses.remove('hidden');
                agentAddressRowClasses.remove('hidden');
                break;
            case 'MAIN_EXPORTER_ACCESS':
                reasonRowClasses.add('hidden');
                agentNameRowClasses.add('hidden');
                agentAddressRowClasses.add('hidden');
                break;
            case 'AGENT_EXPORTER_ACCESS':
                reasonRowClasses.add('hidden');
                agentNameRowClasses.remove('hidden');
                agentAddressRowClasses.remove('hidden');
                break;
        }
        container.scrollIntoView(true);
    };
});

function getClasses(id){
    'use strict';
    return document.getElementById(id).parentElement.parentElement.classList;
}