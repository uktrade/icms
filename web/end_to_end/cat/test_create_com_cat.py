from web.end_to_end import conftest, utils


def test_can_create_com_cat(pages: conftest.UserPages) -> None:
    with pages.exp_page() as page:
        # Create a new CFS Certificate Application Template
        page.get_by_role("link", name="Admin").click()
        page.get_by_role("link", name="Certificate Application Templates").click()
        page.get_by_role("link", name="Create Template").click()
        page.get_by_label("Application Type").select_option("COM")
        page.get_by_label("Template Name").click()
        page.get_by_label("Template Name").fill("Test COM Template")
        page.get_by_label("Template Name").press("Tab")
        page.get_by_label("Template Description").fill("Test COM template description")
        page.get_by_label("Sharing").select_option("EDIT")
        page.get_by_role("button", name="Save").click()

        # Now we are on the edit page store the cat_pk.
        cat_pk = utils.get_application_id(page.url, r"cat/edit/(?P<cat_pk>\d+)/", "cat_pk")

        # Go back to list view
        page.get_by_role("link", name="Certificate Application Templates").click()

        # Check edit link
        utils.get_cat_list_row(page, cat_pk).get_by_role("link", name="Edit").click()

        # Update the COM CAT
        page.get_by_label("Template Description").click()
        page.get_by_label("Template Description").fill("Test COM template description updated")
        page.get_by_role("button", name="Save").click()

        # Fill out the COM form
        page.get_by_role("link", name="Certificate of Manufacture").click()
        page.get_by_role("searchbox").click()
        page.get_by_role("option", name="Afghanistan").click()
        page.get_by_role("searchbox").click()
        page.get_by_role("option", name="Albania").click()
        page.get_by_role("searchbox").click()
        page.get_by_role("option", name="Algeria").click()
        page.locator("#id_is_pesticide_on_free_sale_uk").get_by_text("No").click()
        page.locator("#id_is_manufacturer").get_by_text("Yes").click()
        page.get_by_label("Product name").click()
        page.get_by_label("Product name").fill("Test product name")
        page.get_by_label("Product name").press("Tab")
        page.get_by_label("Chemical name").fill("Test chemical name")
        page.get_by_label("Chemical name").press("Tab")
        page.get_by_label("Manufacturing process").fill("Test manufacturing process")
        page.get_by_role("button", name="Save").click()

        # Go back to list view
        page.get_by_role("link", name="Certificate Application Templates").click()

        # Create an application from the COM Template
        utils.get_cat_list_row(page, cat_pk).get_by_role("link", name="Create Application").click()
        page.locator("#select2-id_exporter-container").click()
        page.get_by_role("option", name="Dummy exporter").click()
        page.locator("#select2-id_exporter_office-container").get_by_text(
            "-- Select Office"
        ).click()
        page.get_by_role("option", name="Buckingham Palace\nLondon\nSW1A 1AA").click()  # /PS-IGNORE
        page.get_by_role("button", name="Create").click()

        # Check we are on the COM Application Edit view.
        utils.get_application_id(page.url, r"/export/com/(?P<app_pk>\d+)/edit/")

        # Delete the template
        page.get_by_role("link", name="Admin").click()
        page.get_by_role("link", name="Certificate Application Templates").click()
        utils.get_cat_list_row(page, cat_pk).get_by_role("button", name="Archive").click()

        # Restore the template
        page.get_by_label("Status").select_option("False")
        page.get_by_role("button", name="Apply filter").click()
        utils.get_cat_list_row(page, cat_pk).get_by_role("button", name="Restore").click()
        page.get_by_label("Close this message").click()
