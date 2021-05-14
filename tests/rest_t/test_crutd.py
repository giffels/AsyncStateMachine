from tardis.rest import crud
from tardis.plugins.sqliteregistry import SqliteRegistry
from ..utilities.utilities import run_async

from unittest import TestCase
from unittest.mock import MagicMock


class TestCRUD(TestCase):
    def setUp(self) -> None:
        self.sql_registry_mock = MagicMock(spec=SqliteRegistry)

    def test_get_resource_state(self):
        async def mocked_async_execute(sql_query: str, bind_parameters: dict):
            return_values = {
                "test-available-01234567ab": [
                    {"drone_uuid": "test-01234567ab", "state": "AvailableState"}
                ],
                "test-noexists-01234567ab": [],
            }

            return return_values[bind_parameters["drone_uuid"]]

        self.sql_registry_mock.async_execute.side_effect = mocked_async_execute

        self.assertEqual(
            [],
            run_async(
                crud.get_resource_state,
                sql_registry=self.sql_registry_mock,
                drone_uuid="test-noexists-01234567ab",
            ),
        )

        self.sql_registry_mock.async_execute.assert_called_with(
            """
    SELECT R.drone_uuid, RS.state
    FROM Resources R
    JOIN ResourceStates RS ON R.state_id = RS.state_id
    WHERE R.drone_uuid = :drone_uuid""",
            {"drone_uuid": "test-noexists-01234567ab"},
        )

        self.sql_registry_mock.reset_mock()

        self.assertEqual(
            [{"drone_uuid": "test-01234567ab", "state": "AvailableState"}],
            run_async(
                crud.get_resource_state,
                sql_registry=self.sql_registry_mock,
                drone_uuid="test-available-01234567ab",
            ),
        )

        self.sql_registry_mock.async_execute.assert_called_with(
            """
    SELECT R.drone_uuid, RS.state
    FROM Resources R
    JOIN ResourceStates RS ON R.state_id = RS.state_id
    WHERE R.drone_uuid = :drone_uuid""",
            {"drone_uuid": "test-available-01234567ab"},
        )
