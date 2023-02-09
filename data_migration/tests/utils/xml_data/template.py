letter_template = """
<p align="justify" foxid="s35uxe_plpxOXcbR">Dear <MM foxid="s35uxf_plpxOXcbR">CONTACT_NAME</MM></p>
<p align="justify" foxid="s35uxg_plpxOXcbR">
    <b foxid="s35uxh_plpxOXcbR">The importation into the UK from outside the EU and the transfer
        from the EU to the UK of firearms, component parts thereof and ammunition - Import licence
        no. </b>
    <b foxid="s35uxi_plpxOXcbR">
        <MM foxid="s35uxj_plpxOXcbR">LICENCE_NUMBER</MM>
    </b>
</p>
"""

letter_template_cleaned = """
<p align="justify">Dear [[CONTACT_NAME]]</p>
<p align="justify">
    <b>The importation into the UK from outside the EU and the transfer
        from the EU to the UK of firearms, component parts thereof and ammunition - Import licence
        no. </b>
    <b>
        [[LICENCE_NUMBER]]
    </b>
</p>
"""


email_template = """
Dear [[IMPORTER_NAME]]

Please make the following amendments to your request:

[DESCRIBE WHAT UPDATES ARE NEEDED]

Yours sincerely,

[[CASE_OFFICER_NAME]]
"""
