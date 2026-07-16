"""CSV import validation for the complete Rangers-era checklist."""

import unittest

import pandas as pd

from utils.imports import import_identity, normalize_import, partition_import_records


class ImportValidationTests(unittest.TestCase):
    def test_u_166_2020_card_import_succeeds(self) -> None:
        frame = pd.DataFrame([{
            "year": 2020,
            "set_name": "Topps Update",
            "card_number": "U-166",
            "card_name": "Adolis García",
            "status": "Need",
        }])

        records = normalize_import(frame, "user-1", "collection-1")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["year"], 2020)
        self.assertEqual(records[0]["card_number"], "U-166")
        self.assertEqual(records[0]["set_name"], "Topps Update")

    def test_pre_2020_import_is_rejected_with_clear_message(self) -> None:
        frame = pd.DataFrame([{"year": 2019, "set_name": "Test", "card_number": "1"}])
        with self.assertRaisesRegex(ValueError, "2020 or later"):
            normalize_import(frame, "user-1", "collection-1")

    def test_duplicate_identity_uses_all_six_normalized_fields(self) -> None:
        existing = pd.DataFrame([{
            "id": "live-1", "year": 2024, "manufacturer": " Topps ", "set_name": "Chrome Update",
            "card_number": "USC-10", "parallel": "Gold", "serial_number": "50",
        }])
        candidate = {
            "year": 2024.0, "manufacturer": "topps", "set_name": " chrome  update ",
            "card_number": "usc-10", "variation": "gold", "serial_number": "50",
        }
        fresh, duplicates = partition_import_records([candidate], existing)
        self.assertEqual(fresh, [])
        self.assertEqual(duplicates[0][1]["id"], "live-1")

    def test_parallel_and_serial_number_differentiate_cards(self) -> None:
        existing = pd.DataFrame([{
            "year": 2024, "manufacturer": "Topps", "set_name": "Chrome", "card_number": "1",
            "parallel": "Gold", "serial_number": "50",
        }])
        records = [
            {"year": 2024, "manufacturer": "Topps", "set_name": "Chrome", "card_number": "1", "parallel": "Blue", "serial_number": "50"},
            {"year": 2024, "manufacturer": "Topps", "set_name": "Chrome", "card_number": "1", "parallel": "Gold", "serial_number": "25"},
        ]
        fresh, duplicates = partition_import_records(records, existing)
        self.assertEqual(len(fresh), 2)
        self.assertEqual(duplicates, [])

    def test_duplicates_inside_one_csv_are_skipped(self) -> None:
        record = {"year": 2025, "manufacturer": "Topps", "set_name": "Holiday", "card_number": "H1", "parallel": "Base", "serial_number": ""}
        fresh, duplicates = partition_import_records([record, dict(record)], pd.DataFrame())
        self.assertEqual(len(fresh), 1)
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(import_identity(duplicates[0][0]), import_identity(duplicates[0][1]))


if __name__ == "__main__":
    unittest.main()
