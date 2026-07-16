"""Tests for collector search behavior."""

import unittest

import pandas as pd

from utils.filters import searchable_mask


class SearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cards = pd.DataFrame([
            {"year": 2024, "set_name": "Topps Chrome", "card_number": "12", "parallel": "Gold", "serial_number": "50", "category": "Numbered", "notes": "show pickup"},
            {"year": 2025, "set_name": "Bowman", "card_number": "AG", "parallel": "", "serial_number": "", "category": "Autograph", "notes": "wishlist"},
        ])

    def test_searches_all_collector_fields(self) -> None:
        for query in ["2024", "chrome", "12", "gold", "50", "numbered", "pickup"]:
            self.assertEqual(searchable_mask(self.cards, query).tolist(), [True, False])

    def test_search_is_literal_and_case_insensitive(self) -> None:
        self.assertEqual(searchable_mask(self.cards, "BOWMAN").tolist(), [False, True])
        self.assertEqual(searchable_mask(self.cards, "[").tolist(), [False, False])


if __name__ == "__main__":
    unittest.main()
