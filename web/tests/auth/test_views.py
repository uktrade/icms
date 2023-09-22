from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertRedirects


def test_login_redirects_to_workbasket(ilb_admin_user, cw_client):
    client = cw_client

    url = reverse("accounts:login")

    resp = client.post(url, data={"username": "Unknown", "password": "password"})

    assert resp.status_code == 200
    assertInHTML(
        '<div id="login-error"><p>Your username and password didn\'t match. Please try again.</p></div>',
        resp.content.decode("utf-8"),
    )

    resp = client.post(url, {"username": ilb_admin_user.username, "password": "test"})
    assertRedirects(resp, reverse("workbasket"), 302)
