from ..utilities.utilities import async_return, run_async

from httpx import AsyncClient

from unittest import TestCase
from unittest.mock import patch


class TestApp(TestCase):
    mock_sqlite_registry_patcher = None
    mock_crud_patcher = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.mock_sqlite_registry_patcher = patch("tardis.rest.database.SqliteRegistry")
        cls.mock_crud_patcher = patch("tardis.rest.crud")
        cls.mock_sqlite_registry = cls.mock_sqlite_registry_patcher.start()
        cls.mock_crud = cls.mock_crud_patcher.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.mock_sqlite_registry_patcher.stop()
        cls.mock_crud_patcher.stop()

    def setUp(self) -> None:
        from tardis.rest.app import app  # has to be imported after SqliteRegistry patch

        self.client = AsyncClient(app=app, base_url="http://test")

    def tearDown(self) -> None:
        run_async(self.client.aclose)

    def test_get_state(self):
        self.mock_crud.get_resource_state.return_value = async_return(
            return_value=[{"drone_uuid": "test-0123456789", "state": "AvailableState"}]
        )

        response = run_async(self.client.get, "/state/test-0123456789")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"drone_uuid": "test-0123456789", "state": "AvailableState"},
        )

        self.mock_crud.get_resource_state.return_value = async_return(return_value=[])
        response = run_async(self.client.get, "/state/test-invalid")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Drone not found"})
