window.addEventListener("DOMContentLoaded", (event) => {
  const licence_type = document.querySelector("#id_licence_type");
  showLastShipment(licence_type.value);

  licence_type.addEventListener('change', (e) => {
    showLastShipment(e.target.value);
  });
});

const showLastShipment = (licence_type) => {
  const first_shipment_label = document.querySelector('label[for="id_shipment_start_date"]');
  const last_shipment_row = document.querySelector(".row_id_shipment_end_date");

  if (licence_type === 'O') {
    first_shipment_label.innerText = "Date of first shipment";
    last_shipment_row.hidden = false;
  } else {
    first_shipment_label.innerText = "Date of shipment";
    last_shipment_row.querySelector('#id_shipment_end_date').value = "";
    last_shipment_row.hidden = true;
  }
};
