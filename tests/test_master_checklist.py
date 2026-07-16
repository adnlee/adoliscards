"""Tests for canonical checklist identity, audits, and reviewed promotion."""

import unittest

import pandas as pd

from utils.master_checklist import (
    audit_checklist,
    card_number_conflicts,
    exact_duplicates,
    identity_key,
    live_record_from_staging,
    normalize_staging_import,
    promotion_candidates,
    variation_conflicts,
    year_conflicts,
)


def candidate(identifier: str, **overrides) -> dict:
    row = {
        "id": identifier, "year": 2020, "manufacturer": "Topps", "set_name": "Topps Update",
        "card_number": "U-166", "card_name": "Adolis Garcia", "category": "Base",
        "variation": "", "serial_number": "", "priority": "Core", "source_url": "https://example.com/checklist",
        "verification_status": "Pending", "verification_notes": "",
    }
    row.update(overrides)
    return row


class MasterChecklistTests(unittest.TestCase):
    def test_identity_normalizes_case_and_whitespace(self) -> None:
        left = candidate("1")
        right = candidate("2", manufacturer=" TOPPS ", set_name="topps   update", card_number="u-166", variation=" ")
        self.assertEqual(identity_key(left), identity_key(right))
        self.assertEqual(identity_key(left), "2020|topps|topps update|u-166|")

    def test_exact_and_probable_duplicate_audits(self) -> None:
        staged = pd.DataFrame([
            candidate("1"), candidate("2", set_name="topps update"),
            candidate("3", manufacturer="Panini"),
        ])
        audits = audit_checklist(pd.DataFrame(), staged)
        self.assertEqual(set(exact_duplicates(staged)["id"]), {"1", "2"})
        self.assertEqual(set(audits["probable_duplicates"]["id"]), {"3"})

    def test_conflict_categories(self) -> None:
        staged = pd.DataFrame([
            candidate("year-a"), candidate("year-b", year=2021),
            candidate("number-a", variation="Blue", card_number="1"),
            candidate("number-b", variation="Blue", card_number="2"),
            candidate("variation-a", card_number="9", variation="Gold"),
            candidate("variation-b", card_number="9", variation="Silver"),
        ])
        self.assertTrue({"year-a", "year-b"}.issubset(set(year_conflicts(staged)["id"])))
        self.assertTrue({"number-a", "number-b"}.issubset(set(card_number_conflicts(staged)["id"])))
        self.assertTrue({"variation-a", "variation-b"}.issubset(set(variation_conflicts(staged)["id"])))

    def test_promotion_requires_verified_source_unique_and_not_live(self) -> None:
        staged = pd.DataFrame([
            candidate("eligible", verification_status="Verified"),
            candidate("pending", card_number="2"),
            candidate("no-source", card_number="3", verification_status="Verified", source_url=""),
            candidate("already-live", card_number="4", verification_status="Verified"),
        ])
        live = pd.DataFrame([candidate("live", card_number="4", verification_status="")])
        promotable, skipped = promotion_candidates(staged, live)
        self.assertEqual(promotable["id"].tolist(), ["eligible"])
        self.assertEqual(set(skipped["id"]), {"pending", "no-source", "already-live"})
        live_record = live_record_from_staging(promotable.iloc[0], "user", "collection")
        self.assertEqual(live_record["status"], "Need")
        self.assertEqual(live_record["parallel"], "")
        self.assertNotIn("id", live_record)

    def test_non_verified_mapping_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "Only records marked Verified"):
            live_record_from_staging(candidate("pending"), "user", "collection")

    def test_verified_csv_import_preserves_source_metadata(self) -> None:
        frame = pd.DataFrame([{
            "year": 2020, "manufacturer": "Topps", "set_name": "Topps Update", "card_number": "U-166",
            "variation": "Base", "source_url": "https://example.com/verified", "verification_status": "Verified",
            "verification_notes": "Checked against publisher checklist",
        }])
        records = normalize_staging_import(frame, "user", "collection")
        self.assertEqual(records[0]["verification_status"], "Verified")
        self.assertIsNotNone(records[0]["verified_at"])
        self.assertEqual(records[0]["source_url"], "https://example.com/verified")


if __name__ == "__main__":
    unittest.main()
