"""Regression coverage for CardVault database-health calculations."""

import unittest

import pandas as pd

from utils.checklist import duplicate_cards, health_summary, incomplete_records, suspicious_card_number_mask


class DatabaseHealthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cards = pd.DataFrame([
            {"id": "1", "year": 2024, "set_name": "Topps", "card_number": "12", "parallel": "Gold", "category": "Numbered", "status": "Owned", "image_path": "front.jpg", "estimated_value": 20, "price_paid": 10, "storage_location": "Box A"},
            {"id": "2", "year": 2024, "set_name": " topps ", "card_number": "12", "parallel": "gold", "category": "Numbered", "status": "Need", "image_path": "", "estimated_value": 0, "price_paid": 0, "storage_location": ""},
            {"id": "3", "year": 2025, "set_name": "Chrome", "card_number": "?", "parallel": "", "category": "", "status": "Owned", "image_path": None, "estimated_value": None, "price_paid": 0, "storage_location": ""},
            {"id": "4", "year": 2025, "set_name": "Chrome", "card_number": "7", "parallel": "", "category": "Base", "status": "Incoming", "image_path": "x.jpg", "estimated_value": 5, "price_paid": 3, "storage_location": "Binder"},
        ])

    def test_exact_duplicates_are_normalized(self) -> None:
        duplicates = duplicate_cards(self.cards)
        self.assertEqual(set(duplicates["id"]), {"1", "2"})
        self.assertIn("duplicate_key", duplicates)

    def test_health_summary_counts_real_rows(self) -> None:
        result = health_summary(self.cards)
        self.assertEqual(result["total"], 4)
        self.assertEqual(result["owned"], 2)
        self.assertEqual(result["need"], 1)
        self.assertEqual(result["incoming"], 1)
        self.assertEqual(result["missing_front_image"], 2)
        self.assertEqual(result["owned_missing_purchase_price"], 1)
        self.assertEqual(result["owned_missing_storage"], 1)
        self.assertEqual(result["blank_category"], 1)

    def test_incomplete_export_has_issue_labels(self) -> None:
        report = incomplete_records(self.cards)
        self.assertIn("health_issues", report)
        self.assertEqual(set(report["id"]), {"2", "3"})
        self.assertTrue(suspicious_card_number_mask(self.cards).loc[2])


if __name__ == "__main__":
    unittest.main()
