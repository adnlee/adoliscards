"""Regression tests for database-derived CardVault metrics."""

import unittest

import pandas as pd

from utils.checklist import coverage, duplicate_cards
from utils.stats import set_progress, summary, year_progress


class CollectionStatsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cards = pd.DataFrame([
            {"id": "1", "year": 2024, "set_name": "Topps", "card_number": "1", "parallel": "", "status": "Owned", "price_paid": 10, "estimated_value": 20},
            {"id": "2", "year": 2024, "set_name": "Topps", "card_number": "2", "parallel": "", "status": "Need", "price_paid": 0, "estimated_value": 5},
            {"id": "3", "year": 2025, "set_name": "Chrome", "card_number": "1", "parallel": "Gold", "status": "Incoming", "price_paid": 15, "estimated_value": 25},
        ])

    def test_summary_uses_only_supplied_rows(self) -> None:
        result = summary(self.cards)
        self.assertEqual(result["tracked"], 3)
        self.assertEqual(result["owned"], 1)
        self.assertEqual(result["need"], 1)
        self.assertEqual(result["incoming"], 1)
        self.assertEqual(result["invested"], 25)
        self.assertEqual(result["value"], 50)

    def test_progress_totals_are_consistent(self) -> None:
        self.assertEqual(int(year_progress(self.cards)["Total"].sum()), 3)
        self.assertEqual(int(set_progress(self.cards)["Missing"].sum()), 2)

    def test_duplicate_and_coverage_helpers(self) -> None:
        duplicate = pd.concat([self.cards, self.cards.iloc[[0]]], ignore_index=True)
        self.assertEqual(len(duplicate_cards(duplicate)), 2)
        self.assertEqual(coverage(self.cards), 100.0)


if __name__ == "__main__":
    unittest.main()
