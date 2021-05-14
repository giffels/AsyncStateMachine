from tardis.rest.service import RestService
from ..utilities.utilities import async_return, run_async

from unittest import TestCase
from unittest.mock import patch


class TestRestService(TestCase):
    def setUp(self) -> None:
        self.rest_service = RestService()

    @patch("tardis.rest.service.Server")
    def test_run(self, mocked_server):
        mocked_server().serve.return_value = async_return()

        mocked_server.reset_mock()

        run_async(self.rest_service.run)
        mocked_server.assert_called_with(config=self.rest_service._config)
