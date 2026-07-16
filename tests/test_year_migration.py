"""Safety checks for the in-place 2020 year constraint migration."""

import unittest
from pathlib import Path


class YearMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sql = Path("cardvault_year_2020_migration.sql").read_text(encoding="utf-8").lower()
        cls.schema = Path("supabase_setup.sql").read_text(encoding="utf-8").lower()

    def test_migration_replaces_only_named_constraint(self) -> None:
        self.assertIn("drop constraint if exists cards_year_check", self.sql)
        self.assertIn("add constraint cards_year_check", self.sql)
        self.assertIn("check (year >= 2020)", self.sql)

    def test_migration_does_not_recreate_or_drop_table(self) -> None:
        self.assertNotIn("create table", self.sql)
        self.assertNotIn("drop table", self.sql)
        self.assertNotIn("drop index", self.sql)
        self.assertNotIn("auth.", self.sql)

    def test_canonical_schema_accepts_2020(self) -> None:
        self.assertIn("year integer not null check (year >= 2020)", self.schema)
        self.assertNotIn("year integer not null check (year >= 2021)", self.schema)


if __name__ == "__main__":
    unittest.main()
