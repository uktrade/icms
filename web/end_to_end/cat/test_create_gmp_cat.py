from web.end_to_end import conftest, utils


def test_can_create_gmp_cat(pages: conftest.UserPages) -> None:
    with pages.exp_page() as page:
        # Create a new CFS Certificate Application Template
        page.get_by_role("link", name="Admin").click()
        page.get_by_role("link", name="Certificate Application Templates").click()
        page.get_by_role("link", name="Create Template").click()
        page.get_by_label("Application Type").select_option("GMP")
        page.get_by_label("Template Name").click()
        page.get_by_label("Template Name").fill("Test GMP Template")
        page.get_by_label("Template Description").click()
        page.get_by_label("Template Description").fill("Test GMP description")
        page.get_by_label("Sharing").select_option("edit")
        page.get_by_role("button", name="Save").click()

        # Now we are on the edit page store the cat_pk.
        cat_pk = utils.get_application_id(page.url, r"cat/edit/(?P<cat_pk>\d+)/", "cat_pk")

        # Go back to list view
        page.get_by_role("link", name="Certificate Application Templates").click()

        # Check edit link
        utils.get_cat_list_row(page, cat_pk).get_by_role("link", name="Edit").click()

        # Update the GMP CAT
        page.get_by_label("Template Description").click()
        page.get_by_label("Template Description").fill("Test GMP description updated")
        page.get_by_role("button", name="Save").click()

        # Fill out the GMP form
        page.get_by_role("link", name="Certificate of Good").click()
        page.get_by_label("Name of the brand").click()
        page.get_by_label("Name of the brand").fill("Brand name")
        page.locator("#id_is_responsible_person_0").check()
        page.locator("#id_responsible_person_name").click()
        page.locator("#id_responsible_person_name").fill("Name")
        page.locator("#id_responsible_person_postcode").click()
        page.locator("#id_responsible_person_postcode").fill("S122S")
        page.locator("#id_responsible_person_address").click()
        page.locator("#id_responsible_person_address").fill("Address line 1")
        page.locator("#id_responsible_person_country").get_by_text("Great Britain").click()
        page.locator("#id_is_manufacturer_0").check()
        page.locator("#id_manufacturer_name").click()
        page.locator("#id_manufacturer_name").fill("Name")
        page.locator("#id_manufacturer_postcode").click()
        page.locator("#id_manufacturer_postcode").fill("S211S")
        page.locator("#id_manufacturer_address").click()
        page.locator("#id_manufacturer_address").fill("Address line 1")
        page.locator("#id_manufacturer_country_0").check()
        page.get_by_label("ISO").check()
        page.locator("#id_auditor_accredited_0").check()
        page.locator("#id_auditor_certified_0").check()
        page.get_by_role("button", name="Save").click()

        # Go back to list view
        page.get_by_role("link", name="Certificate Application Templates").click()

        # Create an application from the GMP Template
        utils.get_cat_list_row(page, cat_pk).get_by_role("link", name="Create Application").click()
        page.get_by_text("-- Select Exporter").click()
        page.get_by_role("option", name="Dummy exporter").click()
        page.locator("#select2-id_exporter_office-container").get_by_text(
            "-- Select Office"
        ).click()
        page.get_by_role("option", name="Buckingham Palace\nLondon\nSW1A 1AA").click()  # /PS-IGNORE
        page.get_by_role("button", name="Create").click()

        # Check we are on the GMP Application Edit view.
        utils.get_application_id(page.url, r"/export/gmp/(?P<app_pk>\d+)/edit/")

        # Delete the template
        page.get_by_role("link", name="Admin").click()
        page.get_by_role("link", name="Certificate Application Templates").click()
        utils.get_cat_list_row(page, cat_pk).get_by_role("button", name="Archive").click()

        # Restore the template
        page.get_by_label("Status").select_option("False")
        page.get_by_role("button", name="Apply filter").click()
        page.get_by_role("button", name="Restore").click()
        page.get_by_label("Close this message").click()
