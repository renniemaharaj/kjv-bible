import unittest

import script
from script import BookData


class CredibleCheckTests(unittest.TestCase):
    def test_marked_verse_returns_clean_text_and_half_open_spans(self) -> None:
        text, markers = script.marked_verse(
            "¶ ‹I am [the] light› of the world."
        )
        self.assertEqual(text, "I am the light of the world.")
        self.assertEqual(
            markers,
            {
                "paragraph_start": True,
                "added_words": [{"start": 5, "end": 8}],
                "words_of_christ": [{"start": 0, "end": 14}],
            },
        )

    def test_extract_corpus_converts_download_and_removes_markup(self) -> None:
        payload: object = {
            "metadata": {"module": "kjv"},
            "verses": [
                {
                    "book_name": "Genesis",
                    "chapter": 1,
                    "verse": 1,
                    "text": "¶ In the [beginning].",
                },
                {
                    "book_name": "Genesis",
                    "chapter": 1,
                    "verse": 2,
                    "text": "‹And the earth.›",
                },
            ],
        }
        self.assertEqual(
            script.extract_comparison_artifacts(
                payload, {"Genesis": (1, 2)}
            ).corpus,
            {
                "Genesis": {
                    "1": {
                        "1": "In the beginning.",
                        "2": "And the earth.",
                    }
                }
            },
        )

    def test_extract_corpus_rejects_wrong_module(self) -> None:
        with self.assertRaisesRegex(script.ApiError, "module"):
            script.extract_comparison_artifacts(
                {"metadata": {"module": "other"}, "verses": []}
            )

    def test_discrepancy_records_reports_exact_reference_and_text(self) -> None:
        local: BookData = {"1": {"1": "Same", "2": "Local punctuation."}}
        credible: BookData = {"1": {"1": "Same", "2": "Local punctuation!"}}
        self.assertEqual(
            script.discrepancy_records("Test", local, credible),
            [
                {
                    "reference": "Test 1:2",
                    "local": "Local punctuation.",
                    "provider": "Local punctuation!",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
