"""Static safety checks for the additive checklist-staging migration."""

import unittest
from pathlib import Path


class StagingMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sql = Path("cardvault_checklist_staging_migration.sql").read_text(encoding="utf-8").lower()

    def test_is_additive_and_preserves_live_records(self) -> None:
        self.assertIn("create table if not exists public.checklist_staging", self.sql)
        self.assertIn("add column if not exists manufacturer", self.sql)
        self.assertNotIn("drop table", self.sql)
        self.assertNotIn("delete from", self.sql)
        self.assertNotIn("update public.cards", self.sql)
        self.assertNotIn("drop index", self.sql)

    def test_staging_has_verification_metadata_and_rls(self) -> None:
        for column in ["source_url", "verification_status", "verified_at", "verification_notes"]:
            self.assertIn(column, self.sql)
        self.assertIn("enable row level security", self.sql)
        self.assertIn("auth.uid()", self.sql)

    def test_identity_columns_are_present(self) -> None:
        for column in ["year", "manufacturer", "set_name", "card_number", "variation"]:
            self.assertIn(column, self.sql)


if __name__ == "__main__":
    unittest.main()
