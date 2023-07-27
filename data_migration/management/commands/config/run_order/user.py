from data_migration import models as dm
from data_migration import queries
from data_migration.management.commands._types import M2M, QueryModel, SourceTarget
from data_migration.utils import xml_parser
from web import models as web

user_source_target = [
    SourceTarget(dm.User, web.User),
    SourceTarget(dm.Email, web.Email),
    SourceTarget(dm.PhoneNumber, web.PhoneNumber),
    SourceTarget(dm.Mailshot, web.Mailshot),
    SourceTarget(dm.Importer, web.Importer),
    SourceTarget(dm.Exporter, web.Exporter),
    SourceTarget(dm.Office, web.Office),
    SourceTarget(dm.Process, web.Process),
    SourceTarget(dm.FurtherInformationRequest, web.FurtherInformationRequest),
    SourceTarget(dm.AccessRequest, web.AccessRequest),
    SourceTarget(dm.ImporterAccessRequest, web.ImporterAccessRequest),
    SourceTarget(dm.ExporterAccessRequest, web.ExporterAccessRequest),
    SourceTarget(dm.ApprovalRequest, web.ApprovalRequest),
    SourceTarget(dm.ImporterApprovalRequest, web.ImporterApprovalRequest),
    SourceTarget(dm.ExporterApprovalRequest, web.ExporterApprovalRequest),
]

user_query_model = [
    QueryModel(queries.users, "users", dm.User),
    QueryModel(queries.importers, "importers", dm.Importer),
    QueryModel(queries.importer_offices, "importer_offices", dm.Office),
    QueryModel(queries.exporters, "exporters", dm.Exporter),
    QueryModel(queries.exporter_offices, "exporter_offices", dm.Office),
    QueryModel(queries.access_requests, "access_requests", dm.AccessRequest),
]

user_m2m = [
    M2M(dm.Office, web.Importer, "offices"),
    M2M(dm.Office, web.Exporter, "offices"),
    M2M(dm.FurtherInformationRequest, web.AccessRequest, "further_information_requests"),
]

user_xml = [
    xml_parser.PhoneNumberParser,
    xml_parser.PersonalEmailAddressParser,
    xml_parser.AlternativeEmailAddressParser,
    xml_parser.ApprovalRequestParser,
    xml_parser.AccessFIRParser,
]
