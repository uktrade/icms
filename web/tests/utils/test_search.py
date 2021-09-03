import datetime
from typing import TYPE_CHECKING

from pytest import fixture

from web.domains.case._import.derogations.models import DerogationsApplication
from web.domains.case._import.models import ImportApplicationType
from web.domains.case._import.wood.models import WoodQuotaApplication
from web.domains.case.models import ApplicationBase
from web.domains.case.views import get_application_current_task
from web.flow.models import Task
from web.types import AuthenticatedHttpRequest, ICMSMiddlewareContext
from web.utils.search import ImportResultRow, SearchTerms, search_applications

if TYPE_CHECKING:
    from web.models import User
    from web.domains.importer.models import Importer

from typing import NamedTuple


class FixtureData(NamedTuple):
    importer: "Importer"
    agent_importer: "Importer"
    importer_user: "User"
    request: AuthenticatedHttpRequest


@fixture
def test_data(db, importer, agent_importer, test_import_user, request):
    request.user = test_import_user
    request.icms = ICMSMiddlewareContext()

    return FixtureData(importer, agent_importer, test_import_user, request)


def test_filter_by_application_type(test_data: FixtureData):
    _create_wood_application("Wood ref 1", test_data)
    _create_wood_application("Wood ref 2", test_data)
    _create_derogation_application("Derogation ref 1", test_data)
    _create_derogation_application("Derogation ref 2", test_data)

    terms = SearchTerms(case_type="import", app_type=ImportApplicationType.Types.WOOD_QUOTA)
    results = search_applications(terms)

    assert results.total_rows == 2

    check_application_references(results.records, "Wood ref 2", "Wood ref 1")


def test_filter_wood(test_data: FixtureData):
    """Do several tests related to searching for wood queries.

    All tests run in a single test for speed.
    The created applications are therefore reused in several tests.
    """

    _test_fetch_all(test_data)

    _test_search_by_case_reference(test_data)

    _test_search_by_status()

    _test_search_by_response_decision()

    _test_search_by_importer_or_agent_name(test_data)

    _test_search_by_submitted_datetime(test_data)

    _test_search_by_licence_date()


def test_order_and_limit_works(test_data: FixtureData):
    """Create many applications and ensure only the latest n submitted are returned"""

    applications = (
        "wood app 1",
        "wood app 2",
        "derogation app 1",
        "derogation app 2",
        "wood app 3",
        "wood app 4",
        "wood app 5",
        "derogation app 3",
        "derogation app 4",
        "derogation app 5",
    )

    for app_ref in applications:
        if app_ref.startswith("wood"):
            _create_wood_application(app_ref, test_data)

        elif app_ref.startswith("derogation"):
            _create_derogation_application(app_ref, test_data)

        else:
            raise Exception(f"failed to create: {app_ref}")

    terms = SearchTerms(case_type="import")
    search_data = search_applications(terms, limit=5)

    assert search_data.total_rows == 10

    assert len(search_data.records) == 5

    check_application_references(
        search_data.records,
        "derogation app 5",
        "derogation app 4",
        "derogation app 3",
        "wood app 5",
        "wood app 4",
    )


def _test_fetch_all(test_data: FixtureData):
    _create_wood_application("Wood in progress", test_data, submit=False)
    _create_wood_application("Wood ref 1", test_data)
    _create_wood_application("Wood ref 2", test_data)

    search_terms = SearchTerms(case_type="import", app_type=ImportApplicationType.Types.WOOD_QUOTA)
    results = search_applications(search_terms)

    assert results.total_rows == 2

    check_application_references(results.records, "Wood ref 2", "Wood ref 1")


def _test_search_by_case_reference(test_data: FixtureData):
    """Test submitting an application and searching for it by the case reference"""

    application = _create_wood_application("Wood ref 3", test_data)
    case_reference = application.get_reference()

    assert case_reference != "Not Assigned"

    search_terms = SearchTerms(
        case_type="import", app_type=ImportApplicationType.Types.WOOD_QUOTA, case_ref=case_reference
    )
    results = search_applications(search_terms)

    assert results.total_rows == 1
    check_application_references(results.records, "Wood ref 3")


def _test_search_by_status():
    """Search by status using the records we have already created"""
    # TODO: Revisit this when doing ICMSLST-1036

    search_terms = SearchTerms(
        case_type="import",
        app_type=ImportApplicationType.Types.WOOD_QUOTA,
        case_status=ApplicationBase.Statuses.SUBMITTED,
    )
    results = search_applications(search_terms)

    assert results.total_rows == 3
    check_application_references(results.records, "Wood ref 3", "Wood ref 2", "Wood ref 1")


def _test_search_by_response_decision():
    submitted_application = WoodQuotaApplication.objects.get(applicant_reference="Wood ref 3")
    submitted_application.decision = ApplicationBase.APPROVE
    submitted_application.save()

    search_terms = SearchTerms(
        case_type="import",
        app_type=ImportApplicationType.Types.WOOD_QUOTA,
        response_decision=ApplicationBase.REFUSE,
    )
    results = search_applications(search_terms)

    assert results.total_rows == 0

    search_terms = SearchTerms(
        case_type="import",
        app_type=ImportApplicationType.Types.WOOD_QUOTA,
        response_decision=ApplicationBase.APPROVE,
    )
    results = search_applications(search_terms)

    assert results.total_rows == 1

    check_application_references(results.records, "Wood ref 3")


def _test_search_by_importer_or_agent_name(test_data: FixtureData):
    search_terms = SearchTerms(
        case_type="import",
        app_type=ImportApplicationType.Types.WOOD_QUOTA,
        importer_agent_name="Not valid",
    )
    results = search_applications(search_terms)

    assert results.total_rows == 0

    search_terms = SearchTerms(
        case_type="import",
        app_type=ImportApplicationType.Types.WOOD_QUOTA,
        importer_agent_name=test_data.importer.name,
    )
    results = search_applications(search_terms)

    assert results.total_rows == 3

    check_application_references(results.records, "Wood ref 3", "Wood ref 2", "Wood ref 1")

    # Set an agent on the first application and check we can search for that.
    application = WoodQuotaApplication.objects.get(applicant_reference="Wood ref 1")
    application.agent = test_data.agent_importer
    application.save()

    search_terms = SearchTerms(
        case_type="import",
        app_type=ImportApplicationType.Types.WOOD_QUOTA,
        importer_agent_name=test_data.agent_importer.name,
    )
    results = search_applications(search_terms)

    assert results.total_rows == 1

    check_application_references(results.records, "Wood ref 1")


def _test_search_by_submitted_datetime(test_data: FixtureData):
    application = _create_wood_application("Wood ref 4", test_data)

    application.submit_datetime = datetime.datetime(2020, 1, 1, 23, 59, 59)
    application.save()

    search_terms = SearchTerms(
        case_type="import",
        app_type=ImportApplicationType.Types.WOOD_QUOTA,
        submitted_datetime_start=datetime.datetime(2020, 1, 2),
    )
    results = search_applications(search_terms)

    assert results.total_rows == 3

    check_application_references(results.records, "Wood ref 3", "Wood ref 2", "Wood ref 1")

    # Now search by end date to only find "Wood ref 4"
    search_terms = SearchTerms(
        case_type="import",
        app_type=ImportApplicationType.Types.WOOD_QUOTA,
        submitted_datetime_start=datetime.datetime(2020, 1, 1),
        submitted_datetime_end=datetime.datetime(2020, 1, 2),
    )
    results = search_applications(search_terms)

    assert results.total_rows == 1

    check_application_references(results.records, "Wood ref 4")


def _test_search_by_licence_date():
    # Set the licence dates on a submitted application (26/AUG/2021 - 26/FEB/2022)
    application = WoodQuotaApplication.objects.get(applicant_reference="Wood ref 4")
    application.licence_start_date = datetime.date(2021, 8, 26)
    application.licence_end_date = datetime.date(2022, 2, 26)
    application.save()

    # Should find the record when the search terms are the same day as the licence dates
    search_terms = SearchTerms(
        case_type="import",
        app_type=ImportApplicationType.Types.WOOD_QUOTA,
        licence_date_start=datetime.date(2021, 8, 26),
        licence_date_end=datetime.date(2022, 2, 26),
    )

    results = search_applications(search_terms)

    assert results.total_rows == 1

    check_application_references(results.records, "Wood ref 4")

    # A later start date should remove the above record
    search_terms = SearchTerms(
        case_type="import",
        app_type=ImportApplicationType.Types.WOOD_QUOTA,
        licence_date_start=datetime.date(2021, 8, 27),
        licence_date_end=datetime.date(2022, 2, 26),
    )
    results = search_applications(search_terms)

    assert results.total_rows == 0

    # an earlier end date should remove the above record
    search_terms = SearchTerms(
        case_type="import",
        app_type=ImportApplicationType.Types.WOOD_QUOTA,
        licence_date_start=datetime.date(2021, 8, 26),
        licence_date_end=datetime.date(2022, 2, 25),
    )
    results = search_applications(search_terms)

    assert results.total_rows == 0


def check_application_references(
    applications: list[ImportResultRow], *references, sort_results=False
):
    """Check the returned applications match the supplied references

    Sort results if we don't care about the order
    """

    expected = sorted(references) if sort_results else list(references)

    actual = (app.case_status.applicant_reference for app in applications)
    actual = sorted(actual) if sort_results else list(actual)

    assert expected == actual


def _create_wood_application(reference, test_data: FixtureData, submit=True):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.WOOD_QUOTA
    )
    process_type = ImportApplicationType.ProcessTypes.WOOD.value

    return _create_application(application_type, process_type, reference, test_data, submit)


def _create_derogation_application(reference, test_data: FixtureData, submit=True):
    application_type = ImportApplicationType.objects.get(
        type=ImportApplicationType.Types.DEROGATION
    )
    process_type = ImportApplicationType.ProcessTypes.DEROGATIONS.value

    return _create_application(application_type, process_type, reference, test_data, submit)


def _create_application(application_type, process_type, reference, test_data, submit):
    kwargs = {
        "applicant_reference": reference,
        "importer": test_data.importer,
        "created_by": test_data.importer_user,
        "last_updated_by": test_data.importer_user,
        "submitted_by": test_data.importer_user,
        "application_type": application_type,
        "process_type": process_type,
        "contact": test_data.importer_user,
    }

    models = {
        ImportApplicationType.ProcessTypes.DEROGATIONS: DerogationsApplication,
        ImportApplicationType.ProcessTypes.WOOD: WoodQuotaApplication,
    }

    model_cls = models[process_type]

    application = model_cls.objects.create(**kwargs)
    Task.objects.create(
        process=application, task_type=Task.TaskType.PREPARE, owner=test_data.importer_user
    )

    if submit:
        _submit_application(application, test_data)

    return application


def _submit_application(application, test_data: FixtureData):
    """Helper function to submit an application (Using the application code to do so)"""
    task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

    application.submit_application(test_data.request, task)
    application.save()
