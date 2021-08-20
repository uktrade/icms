window.addEventListener('load', (event) => {
  const boughtFrom = document.querySelector('#id_know_bought_from');
  const boughtFromInfoBox = document.querySelector('#know-bought-from-info-box');

  boughtFrom.addEventListener('change', (e) => {
    const displayStyle = e.target.value == 'false' ? 'block': 'none';
    boughtFromInfoBox.style.display = displayStyle;
  });

});
