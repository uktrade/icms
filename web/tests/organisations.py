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
            [ImpOP.manage_contacts_and_agents, ImpOP.edit, ImpOP.view],
        ),
        ImporterContact(
            "I1_inactive_contact",
            [ImpOP.manage_contacts_and_agents, ImpOP.edit, ImpOP.view],
            is_active=False,
        ),
    ],
    agents=[
        AgentImporter(
            importer_name="Test Importer 1 Agent 1",
            offices=[
                Office(
                    address_1="I1_A1 address line 1",
                    address_2="I1_A1 address line 2",
                    postcode="EH519HF",  # /PS-IGNORE
                )
            ],
            contacts=[
                ImporterContact("I1_A1_main_contact", [ImpOP.edit, ImpOP.view]),
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
            [ImpOP.manage_contacts_and_agents, ImpOP.edit, ImpOP.view],
        )
    ],
    agents=[],
)

IMPORTER_THREE = TestImporter(
    importer_name="Test Importer 3 Inactive",
    eori_number="GB3333333333ABCDE",
    is_active=False,
    offices=[
        Office(
            address_1="I3 address line 1",
            address_2="I3 address line 2",
            postcode="S120SG",  # /PS-IGNORE
        ),
    ],
    contacts=[
        ImporterContact(
            "I3_inactive_contact",
            [ImpOP.manage_contacts_and_agents, ImpOP.edit, ImpOP.view],
            is_active=False,
        )
    ],
    agents=[],
    type="INDIVIDUAL",
)

IMPORTER_INDIVIDUAL = TestImporter(
    importer_name="",
    eori_number="GB123412341234",
    offices=[
        Office(
            address_1="1 Individual Road",
            address_2="Individual City",
            postcode="XX12 3XX",  # /PS-IGNORE
        ),
    ],
    contacts=[
        ImporterContact(
            "individual_importer_user",
            [ImpOP.manage_contacts_and_agents, ImpOP.edit, ImpOP.view],
        )
    ],
    agents=[],
    type="INDIVIDUAL",
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
            [ExpOP.manage_contacts_and_agents, ExpOP.edit, ExpOP.view],
        ),
        ExporterContact(
            "E1_inactive_contact",
            [ExpOP.manage_contacts_and_agents, ExpOP.edit, ExpOP.view],
            is_active=False,
        ),
        ExporterContact(
            "E1_secondary_contact",
            [ExpOP.manage_contacts_and_agents, ExpOP.edit, ExpOP.view],
        ),
    ],
    exclusive_correspondence=True,
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
                ExporterContact("E1_A1_main_contact", [ExpOP.edit, ExpOP.view]),
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
            [ExpOP.manage_contacts_and_agents, ExpOP.edit, ExpOP.view],
        )
    ],
    agents=[],
)

EXPORTER_THREE = TestExporter(
    exporter_name="Test Exporter 3 Inactive",
    registered_number="333",
    is_active=False,
    offices=[
        Office(
            address_1="E3 address line 1",
            address_2="E3 address line 2",
            postcode="ZE29NQ",  # /PS-IGNORE
        ),
    ],
    contacts=[
        ExporterContact(
            "E3_inactive_contact",
            [ExpOP.manage_contacts_and_agents, ExpOP.edit, ExpOP.view],
            is_active=False,
        )
    ],
    type="INDIVIDUAL",
    agents=[],
)


TEST_IMPORTERS: list[TestImporter] = [
    IMPORTER_ONE,
    IMPORTER_TWO,
    IMPORTER_THREE,
    IMPORTER_INDIVIDUAL,
]
TEST_EXPORTERS: list[TestExporter] = [EXPORTER_ONE, EXPORTER_TWO, EXPORTER_THREE]
