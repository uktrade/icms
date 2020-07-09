$(document).ready(function() {

    var path= window.location.pathname;
    var request_type = $('select#id_request_type')
    var agent_name = $('.row_id_agent_name');
    var agent_address = $('.row_id_agent_address');


    function hide_agent_inputs() {
      console.log('hiding')
      console.log(agent_name)
        agent_name.hide()
        agent_address.hide()
    }
    function show_agent_inputs() {
      console.log('showing')
        agent_name.show()
        agent_address.show()
    }

    function toggle_agent(request_type) {
      console.log(request_type)
      if (request_type == 'MAIN_IMPORTER_ACCESS' || request_type == 'MAIN_EXPORTER_ACCESS') {
        hide_agent_inputs()
      } else {
        show_agent_inputs()
      }
    }

    function on_request_type_change(evt) {
      /*
       * Show/hide agent name/address inputs based  on selected request type
       * */
      toggle_agent(request_type.val())
    }


    function initialise() {
      var type = request_type.val()
      toggle_agent(type)
    }

    
    if(path=='/access/exporter/request/' || path=='/access/importer/request/') {
      initialise()
      request_type.change(on_request_type_change);
    }
});
