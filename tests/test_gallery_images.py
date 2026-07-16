"""Regression tests for fixed-size, non-cropping gallery image frames."""

import unittest
from pathlib import Path

from components.card_tile import media_frame_html


class GalleryImageTests(unittest.TestCase):
    def test_all_source_shapes_use_the_same_frame_markup(self) -> None:
        sources = {
            "portrait": "https://images.example/portrait-600x900.jpg",
            "landscape": "https://images.example/landscape-1200x600.jpg",
            "square": "https://images.example/square-800x800.jpg",
            "front-back composite": "https://images.example/front-back-1600x800.jpg",
        }
        for label, url in sources.items():
            with self.subTest(label=label):
                markup = media_frame_html(url, label)
                self.assertIn('class="cv-card-image-frame"', markup)
                self.assertIn(f'src="{url}"', markup)
                self.assertIn(f'alt="{label}"', markup)

    def test_image_attributes_are_escaped(self) -> None:
        markup = media_frame_html('https://example.test/a.jpg?x=1&name="card"', 'A "card"')
        self.assertIn("&amp;", markup)
        self.assertIn("&quot;card&quot;", markup)

    def test_placeholder_uses_identical_frame(self) -> None:
        markup = media_frame_html(None)
        self.assertIn("cv-card-image-frame", markup)
        self.assertIn("cv-card-image-placeholder", markup)

    def test_css_preserves_full_image_at_fixed_desktop_and_mobile_heights(self) -> None:
        css = Path("assets/styles.css").read_text(encoding="utf-8").replace(" ", "").lower()
        self.assertIn(".cv-card-image-frame{width:100%;height:325px", css)
        self.assertIn("object-fit:contain", css)
        self.assertIn("align-items:center", css)
        self.assertIn("justify-content:center", css)
        self.assertIn("@media(max-width:1100px){.cv-card-image-frame{height:300px}}", css)
        self.assertIn(".cv-card-image-frame{height:270px}", css)

    def test_detail_uses_the_same_shared_frame(self) -> None:
        markup = media_frame_html("https://example.test/front.jpg", detail=True)
        self.assertIn("cv-card-image-frame", markup)
        self.assertIn("cv-detail-image-frame", markup)


if __name__ == "__main__":
    unittest.main()
