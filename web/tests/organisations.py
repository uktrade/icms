from web.permissions import ExporterObjectPermissions as ExpOP
from web.permissions import ImporterObjectPermissions as ImpOP

from .types import (
    AgentExporter,
    AgentImporter,
    ExporterContact,
    ImporterContact,
    Office,
    TestExporter,
    TestImporter,
)

#
# Definition of test organisations, agents and contacts
#
IMPORTER_ONE = TestImporter(
    importer_name="Test Importer 1",
    eori_number="GB1111111111ABCDE",
    offices=[
        Office(
            address_1="I1 address line 1",
            address_2="I1 address line 2",
            postcode="BT180LZ",  # /PS-IGNORE
            eori_number="GB0123456789ABCDE",
        ),
    ],
    contacts=[
        ImporterContact(
            "I1_main_contact",
            [ImpOP.manage_contacts_and_agents, ImpOP.edit, ImpOP.view, ImpOP.is_contact],
        ),
        # Existing fixture users
        ImporterContact("test_import_user", [ImpOP.is_contact]),
        ImporterContact("importer_contact", [ImpOP.is_contact]),
    ],
    agents=[
        AgentImporter(
            importer_name="Test Importer 1 Agent 1",
            offices=[
                Office(
                    address_1="I1_A1 address line 1",
                    address_2="I1_A1 address line 2",
                    postcode="EH519HF",  # /PS-IGNORE
                )  # /PS-IGNORE
            ],
            contacts=[
                ImporterContact("I1_A1_main_contact", [ImpOP.edit, ImpOP.view, ImpOP.is_contact]),
                # Existing fixture users
                ImporterContact("test_agent_import_user", [ImpOP.is_contact]),
            ],
        )
    ],
)

IMPORTER_TWO = TestImporter(
    importer_name="Test Importer 2",
    eori_number="GB2222222222ABCDE",
    offices=[
        Office(
            address_1="I2 address line 1",
            address_2="I2 address line 2",
            postcode="S120SG",  # /PS-IGNORE
        ),
    ],
    contacts=[
        ImporterContact(
            "I2_main_contact",
            [ImpOP.manage_contacts_and_agents, ImpOP.edit, ImpOP.view, ImpOP.is_contact],
        )
    ],
    agents=[],
)

EXPORTER_ONE = TestExporter(
    exporter_name="Test Exporter 1",
    registered_number="111",
    offices=[
        Office(
            address_1="E1 address line 1",
            address_2="E1 address line 2",
            postcode="HG15DB",  # /PS-IGNORE
        )
    ],
    contacts=[
        ExporterContact(
            "E1_main_contact",
            [ExpOP.manage_contacts_and_agents, ExpOP.edit, ExpOP.view, ExpOP.is_contact],
        ),
        # Existing fixture users
        ExporterContact("test_export_user", [ExpOP.is_contact]),
        ExporterContact("exporter_contact", [ExpOP.is_contact]),
    ],
    agents=[
        AgentExporter(
            exporter_name="Test Exporter 1 Agent 1",
            registered_number="111A",
            offices=[
                Office(
                    address_1="E1_A1 address line 1",
                    address_2="E1_A1 address line 2",
                    postcode="WF43ER",  # /PS-IGNORE
                ),
            ],
            contacts=[
                ExporterContact("E1_A1_main_contact", [ExpOP.edit, ExpOP.view, ExpOP.is_contact]),
                # Existing fixture users
                ExporterContact("test_agent_export_user", [ExpOP.is_contact]),
            ],
        )
    ],
)

EXPORTER_TWO = TestExporter(
    exporter_name="Test Exporter 2",
    registered_number="222",
    offices=[
        Office(
            address_1="E2 address line 1",
            address_2="E2 address line 2",
            postcode="ZE29NQ",  # /PS-IGNORE
        ),
    ],
    contacts=[
        ExporterContact(
            "E2_main_contact",
            [ExpOP.manage_contacts_and_agents, ExpOP.edit, ExpOP.view, ExpOP.is_contact],
        )
    ],
    agents=[],
)


TEST_IMPORTERS: list[TestImporter] = [IMPORTER_ONE, IMPORTER_TWO]
TEST_EXPORTERS: list[TestExporter] = [EXPORTER_ONE, EXPORTER_TWO]
