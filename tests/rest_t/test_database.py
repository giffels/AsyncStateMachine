from tardis.rest.database import get_sql_registry

from unittest import TestCase
from unittest.mock import patch


class TestDatabase(TestCase):
    @patch("tardis.rest.database.SqliteRegistry")
    def test_get_sql_registry(self, mocked_sqlite_registry):
        self.assertEqual(get_sql_registry()(), mocked_sqlite_registry())
