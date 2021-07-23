window.addEventListener('load', (event) => {
  const exportersWithAgents = JSON.parse(
    document.querySelector("#exporters_with_agents").textContent
  );

  const exporter = document.querySelector('#id_exporter');

  const agentSelect2 = $("#id_agent").djangoSelect2();
  const agentOfficeSelect2 = $("#id_agent_office").djangoSelect2();

  const agentContainer = document.querySelector(".row_id_agent");
  const agentOfficeContainer = document.querySelector(".row_id_agent_office");

  const triggerAgentDropdowns = () => {
    agentSelect2.empty();
    agentOfficeSelect2.empty();

    let displayStyle = exportersWithAgents.includes(parseInt(exporter.value)) ? "block": "none";
      
    agentContainer.style.display = displayStyle;
    agentOfficeContainer.style.display = displayStyle;
  };

  triggerAgentDropdowns();

  // Adding element on value updated by js doesn't trigger the 'change' event
  $("#id_exporter").on("change", (e) => {
    triggerAgentDropdowns();
  });
});
