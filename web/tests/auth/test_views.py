from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertRedirects


def test_login_redirects_to_workbasket(client, ilb_admin_user):
    url = reverse("login")

    resp = client.post(url, data={"username": "Unknown", "password": "password"})

    assert resp.status_code == 200
    assertInHTML(
        '<div id="login-error">Invalid username or password.<br/>N.B passwords are case sensitive</div>',
        resp.content.decode("utf-8"),
    )

    resp = client.post(url, {"username": ilb_admin_user.username, "password": "test"})
    assertRedirects(resp, reverse("workbasket"), 302)
