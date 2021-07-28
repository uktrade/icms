async function postcodeLookup(postCode) {
    const csrftoken = getCookie('csrftoken');

    let formData = new FormData();
    formData.append("postcode", postCode);

    const headers = {
         "X-CSRFToken": csrftoken
    }

    return await fetch(
      API_ENDPOINTS.postcodeAddressLookup,
      { mode: 'same-origin', method: "POST", body: formData, headers: headers}
    );
}
