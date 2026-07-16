"""Safe card and image deletion gateway tests."""

import unittest

from utils.database import delete_card


class _Query:
    def __init__(self, calls): self.calls = calls
    def delete(self): self.calls.append(("delete",)); return self
    def eq(self, column, value): self.calls.append(("eq", column, value)); return self
    def execute(self): self.calls.append(("execute",)); return self


class _Bucket:
    def __init__(self, calls): self.calls = calls
    def remove(self, paths): self.calls.append(("remove", paths))


class _Storage:
    def __init__(self, calls): self.calls = calls
    def from_(self, bucket): self.calls.append(("bucket", bucket)); return _Bucket(self.calls)


class _Client:
    def __init__(self): self.calls = []; self.storage = _Storage(self.calls)
    def table(self, table): self.calls.append(("table", table)); return _Query(self.calls)


class DeleteCardTests(unittest.TestCase):
    def test_deletes_exact_card_then_associated_image(self) -> None:
        client = _Client()
        delete_card(client, "card-1", "user/front.jpg")
        self.assertEqual(client.calls[:4], [("table", "cards"), ("delete",), ("eq", "id", "card-1"), ("execute",)])
        self.assertEqual(client.calls[4:], [("bucket", "card-images"), ("remove", ["user/front.jpg"])])

    def test_card_without_image_does_not_touch_storage(self) -> None:
        client = _Client()
        delete_card(client, "card-2", "")
        self.assertFalse(any(call[0] == "bucket" for call in client.calls))


if __name__ == "__main__":
    unittest.main()
