window.addEventListener('DOMContentLoaded', (event) => {
  const selectedProductRawMaterial = getCheckedRadioValue("any_raw_materials");
  setEndUse(selectedProductRawMaterial);

  const legislationSelect2 = $("#id_legislations").djangoSelect2();
  const productRawMaterialRadios = getRadioElements("any_raw_materials");
  const goodsOnUKMarketRadios = getRadioElements("goods_placed_on_uk_market")
  const exportRadios = getRadioElements("goods_export_only");

  const events = new EditScheduleEventHandler(legislationSelect2);

  // Setup listeners
  productRawMaterialRadios.forEach(
    (radio) => radio.addEventListener('change', (e) => {
      events.productRawMaterialRadiosOnChange(e);
    })
  );

  exportRadios.forEach(
    (radio) => radio.addEventListener('change', (e) => {
      events.exportRadiosOnChange(e)
    })
  );

  legislationSelect2.on("change", (e) => {
    events.legislationsOnChange(e);
  });

  goodsOnUKMarketRadios.forEach(
    (radio) => radio.addEventListener('change', (e) => {
      events.goodsOnUKMarketRadiosOnChange(e)
    })
  );
});


/**
 * Defines all event handler methods and stores related config.
 */
class EditScheduleEventHandler {
  constructor(legislationSelect2) {
    this.legislationSelect2 = legislationSelect2;
    this.legislationConfig = JSON.parse(document.querySelector("#legislation_config").textContent);
  }

  productRawMaterialRadiosOnChange(e) {
    setEndUse(e.target.value);
  }

  exportRadiosOnChange(e) {
    const selectedLegislations = this.legislationSelect2.val();
    const isExportOnly = e.target.value;

    updateIsResponsiblePerson(selectedLegislations, isExportOnly, this.legislationConfig);
  }

  legislationsOnChange(e) {
    const selectedLegislations = this.legislationSelect2.val();
    const isExportOnly = getIsExportOnlyValue();

    updateIsResponsiblePerson(selectedLegislations, isExportOnly, this.legislationConfig);
    showIsBiocidalClaim(selectedLegislations, this.legislationConfig);
  }

  goodsOnUKMarketRadiosOnChange(e) {
    // check to set export only to no.
    const goodsOnUKMarket = e.target.value === "yes"

    // we're about to manually change the value of goods_export_only, so we want to also trigger a change event so the
    // other event handlers can run
    const new_change_event = new Event("change");

    if (goodsOnUKMarket){
      document.querySelector(`input[type=radio][name="goods_export_only"][value="no"]`).checked = true
      document.querySelector(`input[type=radio][name="goods_export_only"][value="no"]`).dispatchEvent(new_change_event)
    } else {
      document.querySelector(`input[type=radio][name="goods_export_only"][value="yes"]`).checked = true
      document.querySelector(`input[type=radio][name="goods_export_only"][value="yes"]`).dispatchEvent(new_change_event)
    }

    const isExportOnly = getIsExportOnlyValue() === "yes";

    // check if we should select the checkbox
    const selectedLegislations = this.legislationSelect2.val();
    const fieldShown = showResponsiblePersonStatement(selectedLegislations, isExportOnly, this.legislationConfig);

    if (!fieldShown) {
      return;
    }

    const checkbox = document.querySelector("#id_schedule_statements_is_responsible_person");
    checkbox.checked = goodsOnUKMarket;
  }
}


function setEndUse (value) {
  const endUse = document.querySelector('#final-product-end-use-wrapper');
  endUse.style.display = value === "yes" ? "block" : "none";
}


function getIsExportOnlyValue() {
  return getCheckedRadioValue("goods_export_only");
}

function getRadioElements(radioName) {
  return document.querySelectorAll(`input[type=radio][name=${radioName}]`);
}

function getCheckedRadioValue(radioName) {
    const selectedRadio = document.querySelector(`input[type=radio][name=${radioName}]:checked`);
    let value = "";

    if (selectedRadio !== null) {
      value = selectedRadio.value;
    }

    return value;
}


/**
 * Either show or hide the schedule-statements-is-responsible-person field depending on the config.
 *
 * @param {Array.<string>} legislations List of selected legislations
 * @param {string} exportOnly
 * @param {Object.<string, {isEUCosmeticsRegulation: boolean}>} config
 */
function updateIsResponsiblePerson(legislations, exportOnly, config) {
  const showField = showResponsiblePersonStatement(legislations, exportOnly, config);

  const wrapper = document.querySelector("#schedule-statements-is-responsible-person-wrapper")
  wrapper.style.display = showField ? "block" : "none";
}


/**
 * Return true if responsible person statement should be shown.
 *
 * @param {Array.<string>} legislations List of selected legislations
 * @param {string} exportOnly value of export only field
 * @param {Object.<string, {isEUCosmeticsRegulation: boolean}>} config
 */
function showResponsiblePersonStatement(legislations, exportOnly, config) {
  let isEUCosmeticsRegulation = false;

  for (const legislation of legislations) {

    if (config.hasOwnProperty(legislation)) {
      let legislationConfig = config[legislation];

      if (legislationConfig.isEUCosmeticsRegulation) {
        isEUCosmeticsRegulation = true;

        break;
      }
    }
  }
  const notExportOnly = exportOnly === "no";

  return isEUCosmeticsRegulation && notExportOnly;
}


/**
 * Return true if responsible person statement should be shown.
 *
 * @param {Array.<string>} legislations List of selected legislations
 * @param {Object.<string, {isBiocidalClaim: boolean}>} config
 */
function showIsBiocidalClaim(legislations, config) {
  let isBiocidalClaim = false;

  for (const legislation of legislations) {

    if (config.hasOwnProperty(legislation)) {
      let legislationConfig = config[legislation];

      if (legislationConfig.isBiocidalClaim) {
        isBiocidalClaim = true;
        break;
      }
    }
  }

  const isBiocidalClaimQuestion = document.querySelector("#biocidal-claim-question-wrapper");
  isBiocidalClaimQuestion.style.display = isBiocidalClaim ? "block" : "none";
}
