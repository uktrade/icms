from web.domains.case._import.fa_sil import models, utils
from web.domains.file.utils import ICMSFileField

section_firearm_model_mapping = {
    "section1": models.SILSupplementaryReportFirearmSection1,
    "section2": models.SILSupplementaryReportFirearmSection2,
    "section5": models.SILSupplementaryReportFirearmSection5,
    "section582-obsolete": models.SILSupplementaryReportFirearmSection582Obsolete,  # /PS-IGNORE
    "section582-other": models.SILSupplementaryReportFirearmSection582Other,  # /PS-IGNORE
    "section_legacy": models.SILSupplementaryReportFirearmSectionLegacy,
}


def test_get_report_upload_firearm_form_class():
    for section_type, model in section_firearm_model_mapping.items():
        form_class = utils._get_report_upload_firearm_form_class(section_type)
        assert form_class.Meta.model == model
        assert "file" in form_class.base_fields
        assert isinstance(form_class.base_fields["file"], ICMSFileField)


def test_get_report_firearm_model():
    for section_type, model in section_firearm_model_mapping.items():
        model_class = utils._get_report_firearm_model(section_type)
        assert model_class == model


def test_get_report_firearm_form_class():
    for section_type, model in section_firearm_model_mapping.items():
        form_class = utils._get_report_firearm_form_class(section_type)
        assert form_class.Meta.model == model
        assert form_class.Meta.fields == ("serial_number", "calibre", "model", "proofing")


def test_section_type_attribute():
    for section_type, model in section_firearm_model_mapping.items():
        assert model.section_type == section_type
