# flake8: noqa
import_contact_xml = """
<SELLER_HOLDER_LIST>
  <SELLER_HOLDER>
    <PERSON_DETAILS>
      <PERSON_TYPE>LEGAL_PERSON</PERSON_TYPE>
      <LEGAL_PERSON_NAME>FIREARMS DEALER</LEGAL_PERSON_NAME>
      <REGISTRATION_NUMBER />
      <FIRST_NAME />
      <SURNAME />
    </PERSON_DETAILS>
    <ADDRESS>
      <STREET_AND_NUMBER>123 FAKE ST</STREET_AND_NUMBER>
      <TOWN_CITY>FAKE CITY</TOWN_CITY>
      <POSTCODE />
      <REGION>FAKE REGION</REGION>
      <COUNTRY>1000</COUNTRY>
    </ADDRESS>
    <IS_DEALER_FLAG>Y</IS_DEALER_FLAG>
    <SELLER_HOLDER_ID>1</SELLER_HOLDER_ID>
    <UPDATE_FLAG />
  </SELLER_HOLDER>
  <SELLER_HOLDER>
    <PERSON_DETAILS>
      <PERSON_TYPE>LEGAL_PERSON</PERSON_TYPE>
      <LEGAL_PERSON_NAME>ANOTHER DELEAR</LEGAL_PERSON_NAME>
      <REGISTRATION_NUMBER />
      <FIRST_NAME />
      <SURNAME />
    </PERSON_DETAILS>
    <ADDRESS>
      <STREET_AND_NUMBER>456 FAKE RD</STREET_AND_NUMBER>
      <TOWN_CITY>FAKE TOWN</TOWN_CITY>
      <POSTCODE />
      <REGION>SOUTH FAKE REGION</REGION>
      <COUNTRY>1000</COUNTRY>
    </ADDRESS>
    <IS_DEALER_FLAG>Y</IS_DEALER_FLAG>
    <SELLER_HOLDER_ID>2</SELLER_HOLDER_ID>
    <UPDATE_FLAG />
  </SELLER_HOLDER>
</SELLER_HOLDER_LIST>
""".strip()


sr_upload_xml = """
<FA_SUPPLEMENTARY_REPORT_LIST>
  <FA_SUPPLEMENTARY_REPORT>
    <FA_SUPPLEMENTARY_REPORT_DETAILS>
      <GOODS_LINE_LIST>
        <GOODS_LINE>
          <GOODS_ITEM_DESC>Firearms, component parts thereof, or ammunition of any applicable commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended.</GOODS_ITEM_DESC>
          <GOODS_ITEM_QUANTITY>100</GOODS_ITEM_QUANTITY>
          <GOOD_ITEM_ID>Firearms, component parts thereof, or ammunition of any applicable commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended.1</GOOD_ITEM_ID>
          <FA_REPORTING_MODE>UPLOAD</FA_REPORTING_MODE>
          <FIREARMS_DETAILS_LIST/>
          <FILE_UPLOAD_LIST>
            <FILE_UPLOAD>
                <FILE_CONTENT>
                  <filename>a file.pdf</filename>
                  <content-type>application/pdf</content-type>
                  <browser-content-type>application/pdf</browser-content-type>
                  <original-file-location>a file.pdf</original-file-location>
                  <size>1234</size>
                  <status>complete</status>
                  <status-message>Upload complete</status-message>
                  <system-message/>
                  <readable-error-message/>
                  <upload-date-time>2021-11-08T08:29:59</upload-date-time>
                  <file-upload-type>file</file-upload-type>
                  <file-id>abcdefg</file-id>
                  <character-encoding>not specified</character-encoding>
                  <diagnostic-info>
                    <filename>a file.pdf</filename>
                    <content-type>application/pdf</content-type>
                    <browser-content-type>application/pdf</browser-content-type>
                    <original-file-location>a file.pdf</original-file-location>
                    <estimated-size>1234</estimated-size>
                    <status>complete</status>
                    <status-message>Upload complete</status-message>
                    <system-message/>
                    <readable-error-message/>
                    <upload-date-time>2021-11-08T08:29:59</upload-date-time>
                    <file-id>abcde</file-id>
                  </diagnostic-info>
                </FILE_CONTENT>
            </FILE_UPLOAD>
          </FILE_UPLOAD_LIST>
          <GOODS_ITEM_SUBMIT/>
        </GOODS_LINE>
      </GOODS_LINE_LIST>
      <MODE_OF_TRANSPORT>AIR</MODE_OF_TRANSPORT>
      <RECEIVED_DATE>2021-10-14</RECEIVED_DATE>
      <REPORT_SELLER_HOLDER>1</REPORT_SELLER_HOLDER>
      <REPORT_SUBMITTED_FLAG>true</REPORT_SUBMITTED_FLAG>
      <SUBMITTED_BY_WUA_ID>2</SUBMITTED_BY_WUA_ID>
      <SUBMITTED_DATETIME>2021-11-08T08:31:34</SUBMITTED_DATETIME>
      <FA_REPORT_ID>1</FA_REPORT_ID>
    </FA_SUPPLEMENTARY_REPORT_DETAILS>
  </FA_SUPPLEMENTARY_REPORT>
</FA_SUPPLEMENTARY_REPORT_LIST>
""".strip()

sr_manual_xml = """
<FA_SUPPLEMENTARY_REPORT_LIST>
  <FA_SUPPLEMENTARY_REPORT>
    <FA_SUPPLEMENTARY_REPORT_DETAILS>
      <GOODS_LINE_LIST>
        <GOODS_LINE>
          <GOODS_ITEM_DESC>Firearms, component parts thereof, or ammunition of any applicable commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended.</GOODS_ITEM_DESC>
          <GOODS_ITEM_QUANTITY>50</GOODS_ITEM_QUANTITY>
          <GOOD_ITEM_ID>Firearms, component parts thereof, or ammunition of any applicable commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended.1</GOOD_ITEM_ID>
          <FA_REPORTING_MODE>MANUAL</FA_REPORTING_MODE>
          <FIREARMS_DETAILS_LIST>
            <FIREARMS_DETAILS>
              <SERIAL_NUMBER>N/A</SERIAL_NUMBER>
              <CALIBRE>6MM</CALIBRE>
              <MAKE_MODEL>A gun barrel</MAKE_MODEL>
              <PROOFING>N</PROOFING>
            </FIREARMS_DETAILS>
            <FIREARMS_DETAILS>
              <SERIAL_NUMBER>123456</SERIAL_NUMBER>
              <CALIBRE>.30</CALIBRE>
              <MAKE_MODEL>A gun</MAKE_MODEL>
              <PROOFING>Y</PROOFING>
            </FIREARMS_DETAILS>
          </FIREARMS_DETAILS_LIST>
          <FILE_UPLOAD_LIST/>
          <GOODS_ITEM_SUBMIT/>
        </GOODS_LINE>
      </GOODS_LINE_LIST>
      <MODE_OF_TRANSPORT>RAIL</MODE_OF_TRANSPORT>
      <RECEIVED_DATE>2021-11-03</RECEIVED_DATE>
      <REPORT_SELLER_HOLDER>1</REPORT_SELLER_HOLDER>
      <REPORT_SUBMITTED_FLAG>true</REPORT_SUBMITTED_FLAG>
      <SUBMITTED_BY_WUA_ID>2</SUBMITTED_BY_WUA_ID>
      <SUBMITTED_DATETIME>2021-11-07T13:41:00</SUBMITTED_DATETIME>
      <FA_REPORT_ID>1</FA_REPORT_ID>
    </FA_SUPPLEMENTARY_REPORT_DETAILS>
  </FA_SUPPLEMENTARY_REPORT>
  <FA_SUPPLEMENTARY_REPORT>
    <HISTORICAL_REPORT_LIST/>
    <FA_SUPPLEMENTARY_REPORT_DETAILS>
      <GOODS_LINE_LIST>
        <GOODS_LINE>
          <GOODS_ITEM_DESC>Firearms, component parts thereof, or ammunition of any applicable commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended.</GOODS_ITEM_DESC>
          <GOODS_ITEM_QUANTITY>100</GOODS_ITEM_QUANTITY>
          <GOOD_ITEM_ID>Firearms, component parts thereof, or ammunition of any applicable commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended.1</GOOD_ITEM_ID>
          <FA_REPORTING_MODE>MANUAL</FA_REPORTING_MODE>
          <FIREARMS_DETAILS_LIST>
            <FIREARMS_DETAILS>
              <SERIAL_NUMBER>Ammunition</SERIAL_NUMBER>
              <CALIBRE>mixed</CALIBRE>
              <MAKE_MODEL>Various</MAKE_MODEL>
              <PROOFING>Y</PROOFING>
            </FIREARMS_DETAILS>
          </FIREARMS_DETAILS_LIST>
          <FILE_UPLOAD_LIST/>
          <GOODS_ITEM_SUBMIT/>
        </GOODS_LINE>
      </GOODS_LINE_LIST>
      <MODE_OF_TRANSPORT/>
      <RECEIVED_DATE/>
      <REPORT_SELLER_HOLDER/>
      <REPORT_SUBMITTED_FLAG>true</REPORT_SUBMITTED_FLAG>
      <SUBMITTED_BY_WUA_ID>2</SUBMITTED_BY_WUA_ID>
      <SUBMITTED_DATETIME>2021-12-20T10:24:30</SUBMITTED_DATETIME>
      <FA_REPORT_ID>1</FA_REPORT_ID>
    </FA_SUPPLEMENTARY_REPORT_DETAILS>
  </FA_SUPPLEMENTARY_REPORT>
</FA_SUPPLEMENTARY_REPORT_LIST>
""".strip()


sr_list = """
<FA_SUPPLEMENTARY_REPORT_LIST>
  <FA_SUPPLEMENTARY_REPORT>
      <HISTORICAL_REPORT_LIST/>
    <FA_SUPPLEMENTARY_REPORT_DETAILS>
      <GOODS_LINE_LIST>
        <GOODS_LINE>
          <GOODS_ITEM_DESC>Firearms, component parts thereof, or ammunition of any applicable commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended.</GOODS_ITEM_DESC>
          <GOODS_ITEM_QUANTITY>100</GOODS_ITEM_QUANTITY>
          <GOOD_ITEM_ID>Firearms, component parts thereof, or ammunition of any applicable commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended.1</GOOD_ITEM_ID>
          <FA_REPORTING_MODE>MANUAL</FA_REPORTING_MODE>
          <FIREARMS_DETAILS_LIST>
            <FIREARMS_DETAILS>
              <SERIAL_NUMBER>Ammunition</SERIAL_NUMBER>
              <CALIBRE>mixed</CALIBRE>
              <MAKE_MODEL>Various</MAKE_MODEL>
              <PROOFING>Y</PROOFING>
            </FIREARMS_DETAILS>
          </FIREARMS_DETAILS_LIST>
          <FILE_UPLOAD_LIST/>
          <GOODS_ITEM_SUBMIT/>
        </GOODS_LINE>
      </GOODS_LINE_LIST>
      <MODE_OF_TRANSPORT/>
      <RECEIVED_DATE/>
      <REPORT_SELLER_HOLDER/>
      <REPORT_SUBMITTED_FLAG>true</REPORT_SUBMITTED_FLAG>
      <SUBMITTED_BY_WUA_ID>1</SUBMITTED_BY_WUA_ID>
      <SUBMITTED_DATETIME>2021-12-20T10:24:30</SUBMITTED_DATETIME>
      <FA_REPORT_ID>1</FA_REPORT_ID>
    </FA_SUPPLEMENTARY_REPORT_DETAILS>
  </FA_SUPPLEMENTARY_REPORT>
</FA_SUPPLEMENTARY_REPORT_LIST>
""".strip()
