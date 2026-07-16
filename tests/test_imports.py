"""CSV import validation for the complete Rangers-era checklist."""

import unittest

import pandas as pd

from utils.imports import normalize_import


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


if __name__ == "__main__":
    unittest.main()
