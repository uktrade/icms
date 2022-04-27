from datetime import datetime

from data_migration import models as dm
from data_migration.utils import xml_parser

from . import xml_data


def test_oil_application_parse_xml():
    data = xml_parser.OILSupplementaryReportParser.parse_xml(
        [(1, xml_data.sr_upload_xml), (2, xml_data.sr_manual_xml)]
    )

    reports = data[dm.OILSupplementaryReport]
    assert len(reports) == 3
    sr1, sr2, sr3 = reports
    assert sr1.transport == "AIR"
    assert sr1.date_received == datetime.strptime("2021-10-14", "%Y-%m-%d").date()
    assert sr1.supplementary_info_id == 1
    assert sr2.transport == "RAIL"
    assert sr2.date_received == datetime.strptime("2021-11-03", "%Y-%m-%d").date()
    assert sr2.supplementary_info_id == 2
    assert sr3.transport is None
    assert sr3.date_received is None
    assert sr3.supplementary_info_id == 2

    data = xml_parser.OILReportFirearmParser.parse_xml(
        [(1, sr1.report_firearms_xml), (2, sr2.report_firearms_xml), (3, sr3.report_firearms_xml)]
    )

    firearms = data[dm.OILSupplementaryReportFirearm]
    assert len(firearms) == 4
    f1, f2, f3, f4 = firearms
    assert f1.is_upload is True
    assert (f1.is_manual and f1.is_no_firearm) is False
    assert f1.report_id == 1

    assert f2.is_manual is True
    assert (f2.is_upload and f2.is_no_firearm) is False
    assert f2.serial_number == "N/A"
    assert f2.calibre == "6MM"
    assert f2.model == "A gun barrel"
    assert f2.proofing == "no"
    assert f2.report_id == 2

    assert f3.is_manual is True
    assert (f3.is_upload and f3.is_no_firearm) is False
    assert f3.serial_number == "123456"
    assert f3.calibre == ".30"
    assert f3.model == "A gun"
    assert f3.proofing == "yes"
    assert f3.report_id == 2

    assert f4.is_manual is True
    assert (f4.is_upload and f4.is_no_firearm) is False
    assert f4.report_id == 3


def test_dfl_goods_parse_xml():
    data = xml_parser.DFLGoodsCertificateParser.parse_xml([(1, xml_data.dfl_goods_cert)])
    goods = data[dm.DFLGoodsCertificate]

    assert len(goods) == 2
    gc1, gc2 = goods

    assert gc1.dfl_application_id == 1
    assert gc1.deactivated_certificate_reference == "REF A"
    assert gc1.goods_description == "Test Commodity A"
    assert gc1.issuing_country_id == 1
    assert gc1.target_id == 1234

    assert gc2.dfl_application_id == 1
    assert gc2.deactivated_certificate_reference == "REF B"
    assert gc2.goods_description == "Test Commodity B"
    assert gc2.issuing_country_id == 2
    assert gc2.target_id == 5678


def test_sil_goods_parse_xml():
    data = xml_parser.SILGoodsParser.parse_xml([(1, xml_data.sil_goods)])

    sec1_goods = data[dm.SILGoodsSection1]
    assert len(sec1_goods) == 1
    sec1 = sec1_goods[0]
    assert sec1.description == "Test Gun"
    assert sec1.quantity == 5
    assert sec1.manufacture is False
    assert sec1.legacy_ordinal == 1

    sec2_goods = data[dm.SILGoodsSection2]
    assert len(sec2_goods) == 1
    sec2 = sec2_goods[0]
    assert sec2.description == "Test Rifle"
    assert sec2.quantity == 5
    assert sec2.manufacture is False
    assert sec2.legacy_ordinal == 2

    sec5_goods = data[dm.SILGoodsSection5]
    assert len(sec5_goods) == 1
    sec5 = sec5_goods[0]
    assert sec5.description == "Test Pistol"
    assert sec5.quantity == 10
    assert sec5.manufacture is False
    assert sec5.subsection == "5_1_ABA"
    assert sec5.legacy_ordinal == 3

    sec5_obs_goods = data[dm.SILGoodsSection582Obsolete]  # /PS-IGNORE
    assert len(sec5_obs_goods) == 1
    sec5_obs = sec5_obs_goods[0]
    assert sec5_obs.description == "Test Revolver"
    assert sec5_obs.obsolete_calibre_id == 444
    assert sec5_obs.quantity == 1
    assert sec5_obs.manufacture is True
    assert sec5_obs.legacy_ordinal == 4

    sec5_other_goods = data[dm.SILGoodsSection582Other]  # /PS-IGNORE
    assert len(sec5_other_goods) == 1
    sec5_other = sec5_other_goods[0]
    assert sec5_other.description == "Test Other"
    assert sec5_other.quantity == 1
    assert sec5_other.manufacture is True
    assert sec5_other.curiosity_ornament is True
    assert sec5_other.ignition is False
    assert sec5_other.ignition_details == ""
    assert sec5_other.ignition_other == ""
    assert sec5_other.bore is False
    assert sec5_other.bore_details == ""
    assert sec5_other.rimfire is True
    assert sec5_other.rimfire_details == ".32 rimfire"
    assert sec5_other.legacy_ordinal == 5
