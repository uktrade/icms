import re

from web.end_to_end import conftest, utils


def test_can_create_cfs_cat(pages: conftest.UserPages) -> None:
    with pages.exp_page() as page:
        # Create a new CFS Certificate Application Template
        page.get_by_role("link", name="Admin").click()
        page.get_by_role("link", name="Certificate Application Templates").click()
        page.get_by_role("link", name="Create Template").click()

        # Wait for page js to load
        page.wait_for_load_state(state="domcontentloaded")
        page.get_by_label("Application Type").select_option("CFS")
        page.get_by_label("Template Country").select_option("GB")

        page.get_by_label("Template Name").click()
        page.get_by_label("Template Name").fill("Test CFS template")
        page.get_by_label("Template Description").click()
        page.get_by_label("Template Description").fill("Test CFS template description")
        page.get_by_label("Sharing").select_option("EDIT")
        page.get_by_role("button", name="Save").click()

        # Now we are on the edit page store the cat_pk.
        cat_pk = utils.get_application_id(page.url, r"cat/edit/(?P<cat_pk>\d+)/", "cat_pk")

        # Go back to list view
        page.get_by_role("link", name="Certificate Application Templates").click()

        # Check edit link
        utils.get_cat_list_row(page, cat_pk).get_by_role("link", name="Edit").click()

        # Update the CFS CAT
        page.get_by_label("Template Description").click()
        page.get_by_label("Template Description").fill("Test CFS template description updated")
        page.get_by_role("button", name="Save").click()

        # Fill out the CFS form
        page.get_by_role("link", name="Certificate of Free Sale").click()
        page.get_by_placeholder("Select Country").click()
        page.get_by_role("option", name="Afghanistan").click()
        page.get_by_role("searchbox").click()
        page.get_by_role("option", name="Albania").click()
        page.get_by_role("button", name="Save").click()

        # Delete the initial schedule
        page.get_by_label("Delete").click()
        page.get_by_role("button", name="OK").click()

        # Add a new schedule
        page.get_by_role("button", name="Add Schedule").click()

        # Edit the only schedule
        page.get_by_role("link", name="Edit schedule").click()

        page.get_by_label("I am the manufacturer").check()
        page.locator("#id_brand_name_holder").get_by_text("Yes").click()
        page.get_by_placeholder("Select Legislation").click()
        page.get_by_role(
            "option", name="Aerosol Dispensers Regulations 2009/ 2824 as applicable in GB"
        ).click()
        page.get_by_label("The products are currently").check()
        page.locator("#id_goods_placed_on_uk_market_0").check()
        page.locator("#id_any_raw_materials_0").check()
        page.get_by_label("End Use or Final Product").click()
        page.get_by_label("End Use or Final Product").fill("Test End Use or Final Product")
        page.get_by_label("Country Of Manufacture").select_option("38")
        page.get_by_label("These products are").check()
        page.get_by_role("button", name="Save").click()

        # Add the manufacturer details to schedule 1
        page.get_by_role("link", name="Add Manufacturer").click()
        page.wait_for_load_state(state="domcontentloaded")
        page.get_by_label("Name").click()
        page.get_by_label("Name").fill("Test Manufacturer")
        page.get_by_text("Manual").click()
        page.get_by_label("Postcode").click()
        page.get_by_label("Postcode").fill("s111S")
        page.get_by_label("Address", exact=True).click()
        page.get_by_label("Address", exact=True).fill("Address line one")
        page.get_by_role("button", name="Save").click()

        # Add, edit and delete a few products.
        page.get_by_role("link", name="Manage Products").click()
        page.get_by_role("button", name="Add product").click()
        page.locator("#id_products-0-product_name").click()
        page.locator("#id_products-0-product_name").fill("product 1")
        page.locator("#id_products-1-product_name").click()
        page.locator("#id_products-1-product_name").fill("Product 2")
        page.get_by_role("button", name="Save").click()
        page.get_by_role("link", name="Manage Products").click()
        page.get_by_role("cell", name="product 1").get_by_label("").click()
        page.get_by_role("cell", name="product 1").get_by_label("").fill("product 1 updated")
        page.get_by_role("cell", name="Product 2").get_by_label("").click()
        page.get_by_role("cell", name="Product 2").get_by_label("").fill("Product 2 updated")
        page.get_by_role("button", name="Save").click()
        page.get_by_role("link", name="Manage Products").click()
        # Delete buttons
        page.get_by_role("cell", name="product 1 updated").get_by_role("button").click()
        page.get_by_role("cell", name="product 2 updated").get_by_role("button").click()
        page.get_by_role("button", name="Save").click()

        # Navigate back to main csf form (showing schedule list)
        page.get_by_role("link", name="Certificate of Free Sale").click()

        # Copy Schedule 1
        page.get_by_label("Copy").click()
        page.get_by_role("button", name="OK").click()

        # Go back to list view
        page.get_by_role("link", name="Certificate Application Templates").click()

        # Create an application from the CFS Template
        utils.get_cat_list_row(page, cat_pk).get_by_role("link", name="Create Application").click()
        page.get_by_text("-- Select Exporter").click()
        page.get_by_role("option", name="Dummy Exporter 1").click()
        page.locator("#select2-id_exporter_office-container").get_by_text(
            "-- Select Office"
        ).click()
        page.get_by_role(
            "option", name="1 Buckingham Palace\nLondon\nSW1A 1AA"  # /PS-IGNORE
        ).click()
        page.get_by_role("button", name="Create").click()

        # Check we are on the CFS Application Edit view.
        utils.get_application_id(page.url, r"/export/cfs/(?P<app_pk>\d+)/edit/")

        # Delete the template
        page.get_by_role("link", name="Admin").click()
        page.get_by_role("link", name="Certificate Application Templates").click()
        utils.get_cat_list_row(page, cat_pk).get_by_role("button", name="Archive").click()

        # Restore the template
        page.get_by_label("Status").select_option("False")
        page.get_by_role("button", name="Apply filter").click()
        utils.get_cat_list_row(page, cat_pk).get_by_role("button", name="Restore").click()
        page.get_by_label("Close this message").click()


def test_can_create_cfs_cat_biocidal_schdedule(pages: conftest.UserPages) -> None:
    with pages.exp_page() as page:
        # Create a new CFS Certificate Application Template
        page.get_by_role("link", name="Admin").click()
        page.get_by_role("link", name="Certificate Application Templates").click()
        page.get_by_role("link", name="Create Template").click()

        # Wait for page js to load
        page.wait_for_load_state(state="domcontentloaded")
        page.get_by_label("Application Type").select_option("CFS")
        page.get_by_label("Template Country").select_option("GB")

        page.get_by_label("Template Name").click()
        page.get_by_label("Template Name").fill("Test CFS template")
        page.get_by_label("Template Description").click()
        page.get_by_label("Template Description").fill("Test CFS template description")
        page.get_by_label("Sharing").select_option("EDIT")
        page.get_by_role("button", name="Save").click()

        # Now we are on the edit page store the cat_pk.
        cat_pk = utils.get_application_id(page.url, r"cat/edit/(?P<cat_pk>\d+)/", "cat_pk")

        # Go back to list view
        page.get_by_role("link", name="Certificate Application Templates").click()

        # Check edit link
        utils.get_cat_list_row(page, cat_pk).get_by_role("link", name="Edit").click()

        # Update the CFS CAT
        page.get_by_label("Template Description").click()
        page.get_by_label("Template Description").fill("Test CFS template description updated")
        page.get_by_role("button", name="Save").click()

        # Fill out the CFS form
        page.get_by_role("link", name="Certificate of Free Sale").click()
        page.get_by_placeholder("Select Country").click()
        page.get_by_role("option", name="Afghanistan").click()
        page.get_by_role("searchbox").click()
        page.get_by_role("option", name="Albania").click()
        page.get_by_role("button", name="Save").click()

        # Delete the initial schedule
        page.get_by_label("Delete").click()
        page.get_by_role("button", name="OK").click()

        # Add a new schedule
        page.get_by_role("button", name="Add Schedule").click()

        # Edit the only schedule
        page.get_by_role("link", name="Edit schedule").click()

        page.get_by_label("I am the manufacturer").check()
        page.locator("#id_brand_name_holder").get_by_text("Yes").click()
        page.get_by_placeholder("Select Legislation").click()

        page.get_by_role(
            "option",
            name=(
                "Regulation (EU) No. 528/2012 of the European Parliament and of the Council concerning the making available on the market and use of"
                " biocidal products, as it has effect in Great Britain"
            ),
        ).click()
        page.get_by_label("The products are currently").check()
        page.locator("#id_goods_placed_on_uk_market_0").check()
        page.locator("#id_goods_export_only_1").check()
        page.locator("#id_any_raw_materials_0").check()
        page.get_by_label("End Use or Final Product").click()
        page.get_by_label("End Use or Final Product").fill("Test End Use or Final Product")
        page.get_by_label("Country Of Manufacture").select_option("38")
        page.get_by_label("These products are").check()
        page.get_by_role("button", name="Save").click()

        # Add the manufacturer details to schedule 1
        page.get_by_role("link", name="Add Manufacturer").click()
        page.wait_for_load_state(state="domcontentloaded")
        page.get_by_label("Name").click()
        page.get_by_label("Name").fill("Test Manufacturer")
        page.get_by_text("Manual").click()
        page.get_by_label("Postcode").click()
        page.get_by_label("Postcode").fill("s111S")
        page.get_by_label("Address", exact=True).click()
        page.get_by_label("Address", exact=True).fill("Address line one")
        page.get_by_role("button", name="Save").click()

        # Add a product to schedule 2
        page.get_by_role("link", name="Manage Products").click()
        page.locator("#id_products-0-product_name").click()
        page.locator("#id_products-0-product_name").fill("Product 1")
        page.get_by_role("button", name="Add product type number").first.click()
        page.locator(
            "#id_product-type-products-0-product_type_numbers-0-product_type_number"
        ).select_option("1")
        page.locator(
            "#id_product-type-products-0-product_type_numbers-1-product_type_number"
        ).select_option("2")
        page.locator("#id_active-ingredient-products-0-active_ingredients-0-name").click()
        page.locator("#id_active-ingredient-products-0-active_ingredients-0-name").fill("Name 1")
        page.locator("#id_active-ingredient-products-0-active_ingredients-0-cas_number").click()
        page.locator("#id_active-ingredient-products-0-active_ingredients-0-cas_number").fill(
            "58-08-2"
        )

        page.get_by_role("button", name=re.compile(r".+Add product$"), include_hidden=False).click()
        page.locator("#id_products-1-product_name").click()
        page.locator("#id_products-1-product_name").fill("Product 2")
        page.locator(
            "#id_product-type-products-1-product_type_numbers-0-product_type_number"
        ).select_option("1")
        page.locator("#id_active-ingredient-products-1-active_ingredients-0-name").fill("Name 2")
        page.locator("#id_active-ingredient-products-1-active_ingredients-0-cas_number").click()
        page.locator("#id_active-ingredient-products-1-active_ingredients-0-cas_number").fill(
            "27039-77-6"
        )
        page.get_by_role("button", name="Save").click()

        page.get_by_role("link", name="Manage Products").click()
        page.get_by_role("cell", name="Product 1").get_by_role("button").click()
        page.get_by_role("cell", name="Product 2").get_by_role("button").click()
        page.get_by_role("button", name="Save").click()

        # Navigate back to main csf form (showing schedule list)
        page.get_by_role("link", name="Certificate of Free Sale").click()

        # Copy Schedule 1
        page.get_by_label("Copy").click()
        page.get_by_role("button", name="OK").click()

        # Go back to list view
        page.get_by_role("link", name="Certificate Application Templates").click()

        # Create an application from the CFS Template
        utils.get_cat_list_row(page, cat_pk).get_by_role("link", name="Create Application").click()
        page.get_by_text("-- Select Exporter").click()
        page.get_by_role("option", name="Dummy Exporter 1").click()
        page.locator("#select2-id_exporter_office-container").get_by_text(
            "-- Select Office"
        ).click()
        page.get_by_role(
            "option", name="1 Buckingham Palace\nLondon\nSW1A 1AA"  # /PS-IGNORE
        ).click()
        page.get_by_role("button", name="Create").click()

        # Check we are on the CFS Application Edit view.
        utils.get_application_id(page.url, r"/export/cfs/(?P<app_pk>\d+)/edit/")

        # Delete the template
        page.get_by_role("link", name="Admin").click()
        page.get_by_role("link", name="Certificate Application Templates").click()
        utils.get_cat_list_row(page, cat_pk).get_by_role("button", name="Archive").click()

        # Restore the template
        page.get_by_label("Status").select_option("False")
        page.get_by_role("button", name="Apply filter").click()
        utils.get_cat_list_row(page, cat_pk).get_by_role("button", name="Restore").click()
        page.get_by_label("Close this message").click()
