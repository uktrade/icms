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
            "option", name="Aerosol Dispensers Regulations 2009/ 2824 as retained in UK law"
        ).click()
        page.get_by_label("The products are currently").check()
        page.locator("#id_goods_placed_on_uk_market_0").check()
        page.locator("#id_goods_export_only_1").check()
        page.locator("#id_any_raw_materials_0").check()
        page.get_by_label("End Use or Final Product").click()
        page.get_by_label("End Use or Final Product").fill("Test End Use or Final Product")
        page.get_by_label("Country Of Manufacture").select_option("1")
        page.get_by_label("These products are").check()
        page.get_by_role("button", name="Save").click()

        # Add the manufacturer details to schedule 1
        page.get_by_role("link", name="Add Manufacturer").click()
        page.get_by_label("Name").click()
        page.get_by_label("Name").press("Shift+CapsLock")
        page.get_by_label("Name").fill("Test Manufacturer")
        page.get_by_label("Postcode").click()
        page.get_by_label("Postcode").fill("s111S")
        page.get_by_label("Address\n        \n          optional").click()
        page.get_by_label("Address\n        \n          optional").fill("Address line one")
        page.get_by_role("button", name="Save").click()

        # Add, edit and delete a product.
        page.get_by_role("link", name="Add Product").click()
        page.get_by_label("Product Name").click()
        page.get_by_label("Product Name").fill("Product 1")
        page.get_by_role("button", name="Create").click()
        product_pk = utils.get_application_id(
            page.url,
            r"cat/edit/\d+/schedule_template/\d+/cfs-schedule-product-update/(?P<product_pk>\d+)/",
            "product_pk",
        )
        page.get_by_label("Product Name").click()
        page.get_by_label("Product Name").fill("Product 1 updated")
        page.get_by_role("button", name="save").click()
        page.get_by_role("link", name="Edit schedule").click()
        utils.get_cfs_product_list_row(page, product_pk).get_by_role(
            "button", name="Delete"
        ).click()

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
        page.get_by_role("option", name="Dummy exporter").click()
        page.locator("#select2-id_exporter_office-container").get_by_text(
            "-- Select Office"
        ).click()
        page.get_by_role("option", name="Buckingham Palace\nLondon\nSW1A 1AA").click()  # /PS-IGNORE
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
            "option", name="Biocide Products Regulation 528/2012 as retained in UK law"
        ).click()
        page.get_by_label("The products are currently").check()
        page.locator("#id_goods_placed_on_uk_market_0").check()
        page.locator("#id_goods_export_only_1").check()
        page.locator("#id_any_raw_materials_0").check()
        page.get_by_label("End Use or Final Product").click()
        page.get_by_label("End Use or Final Product").fill("Test End Use or Final Product")
        page.get_by_label("Country Of Manufacture").select_option("1")
        page.get_by_label("These products are").check()
        page.get_by_role("button", name="Save").click()

        # Add the manufacturer details to schedule 1
        page.get_by_role("link", name="Add Manufacturer").click()
        page.get_by_label("Name").click()
        page.get_by_label("Name").press("Shift+CapsLock")
        page.get_by_label("Name").fill("Test Manufacturer")
        page.get_by_label("Postcode").click()
        page.get_by_label("Postcode").fill("s111S")
        page.get_by_label("Address\n        \n          optional").click()
        page.get_by_label("Address\n        \n          optional").fill("Address line one")
        page.get_by_role("button", name="Save").click()

        # Add, edit and delete several products (including active ingredients / product types.
        page.get_by_role("link", name="Add Product").click()
        page.get_by_label("Product Name").click()
        page.get_by_label("Product Name").fill("Product 1")
        page.get_by_role("button", name="Create").click()
        product_pk = utils.get_application_id(
            page.url,
            r"cat/edit/\d+/schedule_template/\d+/cfs-schedule-product-update/(?P<product_pk>\d+)/",
            "product_pk",
        )
        page.get_by_label("Product Name").click()
        page.get_by_label("Product Name").fill("Test product updated")
        page.locator("#id_pt_-0-product_type_number").select_option("1")
        page.locator("#id_pt_-1-product_type_number").select_option("2")
        page.locator("#id_pt_-2-product_type_number").select_option("3")
        page.locator("#id_ai_-0-name").click()
        page.locator("#id_ai_-0-name").fill("Active ingredient 1")
        page.locator("#id_ai_-0-cas_number").click()
        page.locator("#id_ai_-0-cas_number").fill("111-11-1111")
        page.locator("#id_ai_-1-name").click()
        page.locator("#id_ai_-1-name").fill("Active ingredient 2")
        page.locator("#id_ai_-1-cas_number").click()
        page.locator("#id_ai_-1-cas_number").fill("222-22-2222")
        page.locator("#id_ai_-2-name").click()
        page.locator("#id_ai_-2-name").fill("Active ingredient 3")
        page.locator("#id_ai_-2-cas_number").click()
        page.locator("#id_ai_-2-cas_number").fill("333-33-3333")
        page.get_by_role("button", name="save").click()
        page.locator("#id_pt_-1-DELETE").check()
        page.locator("#id_pt_-2-DELETE").check()
        page.locator("#id_ai_-1-DELETE").check()
        page.locator("#id_ai_-2-DELETE").check()
        page.get_by_role("button", name="save").click()
        page.get_by_role("link", name="Edit schedule").click()
        utils.get_cfs_product_list_row(page, product_pk).get_by_role(
            "button", name="Delete"
        ).click()

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
        page.get_by_role("option", name="Dummy exporter").click()
        page.locator("#select2-id_exporter_office-container").get_by_text(
            "-- Select Office"
        ).click()
        page.get_by_role("option", name="Buckingham Palace\nLondon\nSW1A 1AA").click()  # /PS-IGNORE
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
