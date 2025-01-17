async function endorsementTextLookup(templatePK) {
    const csrftoken = getCookie('csrftoken');
    const headers = {"X-CSRFToken": csrftoken}

    // template_pk is the only mandatory query param for this endpoint.
    // See GetEndorsementTextView class for more details.
    const url = `${endorsementTextURL}?template_pk=${templatePK}`

    return await fetch(
        url, {mode: 'same-origin', method: "GET", headers: headers}
    );
}
