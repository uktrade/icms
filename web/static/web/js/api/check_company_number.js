/**
 * Gets company information from Companies House using the company number
 * @param companyNumber
 * @returns {Promise<Response>}
 * @constructor
 */
async function getCompanyFromCompaniesHouse(companyNumber) {
    const csrftoken = getCookie('csrftoken');
    const headers = {
         "X-CSRFToken": csrftoken
    }

    let formData = new FormData();
    formData.append("company_number", companyNumber);

    return await fetch(
      API_ENDPOINTS.companyNumberLookup,
      { mode: 'same-origin', method: "POST", body: formData, headers: headers}
    );
}
