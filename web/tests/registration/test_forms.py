from web.registration.forms import AccountRecoveryForm


def test_account_recovery_form_valid(legacy_user):
    form = AccountRecoveryForm(
        data={"legacy_email": legacy_user.email, "legacy_password": "TestPassword1!"}
    )

    assert form.is_valid()

    # Check the user is saved to the form data
    assert form.cleaned_data["legacy_user"] == legacy_user


def test_account_recovery_form_invalid_email(db):
    form = AccountRecoveryForm(
        data={
            "legacy_email": "unknown@example.com",  # /PS-IGNORE
            "legacy_password": "TestPassword1!",
        }
    )

    assert not form.is_valid()
    assert len(form.errors) == 1, form.errors

    errors = form.errors.as_data()
    error = errors["__all__"][0].message

    assert error == "Your username and password didn't match. Please try again."


def test_account_recovery_form_invalid_password(db, legacy_user):
    form = AccountRecoveryForm(
        data={"legacy_email": legacy_user.email, "legacy_password": "Invalid"}
    )

    assert not form.is_valid()
    assert len(form.errors) == 1, form.errors

    errors = form.errors.as_data()
    error = errors["__all__"][0].message

    assert error == "Your username and password didn't match. Please try again."


def test_account_recovery_form_invalid_missing_data(db):
    form = AccountRecoveryForm(data={"legacy_email": "", "legacy_password": ""})

    assert not form.is_valid()
    assert len(form.errors) == 2, form.errors

    errors = form.errors.as_data()
    assert errors["legacy_email"][0].message == "You must enter this item"
    assert errors["legacy_password"][0].message == "You must enter this item"
