import sys
import os
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from data.ingest_jsonl import parse_date_info, normalize_criticism_record, aggregate_word_data


class TestIngestPipeline(unittest.TestCase):

    def test_parse_date_epoch_ms(self):
        epoch = 806976000000  # 1995-07-29
        raw_epoch, date_str, year = parse_date_info(epoch)
        self.assertEqual(raw_epoch, epoch)
        self.assertEqual(date_str, "1995-07-29")
        self.assertEqual(year, 1995)

    def test_parse_date_strings_and_nulls(self):
        _, date_str1, year1 = parse_date_info("1998-08-12")
        self.assertEqual(date_str1, "1998-08-12")
        self.assertEqual(year1, 1998)

        _, date_str2, year2 = parse_date_info(None)
        self.assertIsNone(date_str2)
        self.assertIsNone(year2)

        _, date_str3, year3 = parse_date_info("")
        self.assertIsNone(date_str3)
        self.assertIsNone(year3)

    def test_normalize_criticism_record_standard(self):
        raw = {
            "Id": "test_1",
            "Author": "Brown, Geoff",
            "Title": "Test Title",
            "Publication": "The Times",
            "Date": 806976000000,
            "Place": "London",
            "Full_text": "A full text with words",
            "extracted_text": "Extracted text",
            "URL": "http://example.com",
            "Category": "Films",
            "Sentiment": "Positive",
            "Summary": "A great movie review",
            "LLM_Artists_Percentages": {"Christina Ricci": 5.0, "Sam Neill": 4.0},
            "Found_Concepts": ["delighted", "emotional"],
            "Concept_Snippets": {
                "delighted": ["Snippet 1"],
                "emotional": ["Snippet 2"]
            }
        }
        normalized = normalize_criticism_record(raw)
        self.assertEqual(normalized["_id"], "test_1")
        self.assertEqual(normalized["Author"], "Brown, Geoff")
        self.assertEqual(normalized["Title"], "Test Title")
        self.assertEqual(normalized["DateEpoch"], 806976000000)
        self.assertEqual(normalized["DateStr"], "1995-07-29")
        self.assertEqual(normalized["Year"], 1995)
        self.assertEqual(normalized["ArtistsList"], ["Christina Ricci", "Sam Neill"])
        self.assertEqual(normalized["LLM_Artists_Percentages"]["Christina Ricci"], 5.0)
        self.assertEqual(normalized["Found_Concepts"], ["delighted", "emotional"])
        self.assertEqual(normalized["Concept_Snippets"]["delighted"], ["Snippet 1"])

    def test_normalize_criticism_record_edge_cases(self):
        raw_empty = {
            "Id": "test_empty",
            "Author": None,
            "Title": None,
            "Date": None,
            "LLM_Artists_Percentages": None,
            "Found_Concepts": None,
            "Concept_Snippets": None
        }
        normalized = normalize_criticism_record(raw_empty)
        self.assertEqual(normalized["_id"], "test_empty")
        self.assertIsNone(normalized["Author"])
        self.assertEqual(normalized["Title"], "Untitled")
        self.assertEqual(normalized["Category"], "Uncategorized")
        self.assertEqual(normalized["Sentiment"], "Neutral")
        self.assertEqual(normalized["ArtistsList"], [])
        self.assertEqual(normalized["LLM_Artists_Percentages"], {})
        self.assertEqual(normalized["Found_Concepts"], [])
        self.assertEqual(normalized["Concept_Snippets"], {})

    def test_aggregate_word_data(self):
        docs = [
            {
                "Found_Concepts": ["beautiful", "profound"],
                "Category": "Concerts",
                "Sentiment": "Positive",
                "Year": 1995,
                "ArtistsList": ["Harold Pinter"],
                "Concept_Snippets": {"beautiful": ["A beautiful line"]}
            },
            {
                "Found_Concepts": ["beautiful"],
                "Category": "Theater",
                "Sentiment": "Neutral",
                "Year": 1995,
                "ArtistsList": ["Harold Pinter", "Harriet Walter"],
                "Concept_Snippets": {"beautiful": ["Another beautiful line"]}
            }
        ]
        results = aggregate_word_data(docs)
        self.assertEqual(len(results), 2)

        beautiful = next(r for r in results if r["Word"] == "beautiful")
        self.assertEqual(beautiful["TotalCount"], 2)
        self.assertEqual(beautiful["YearCounts"]["1995"], 2)
        self.assertEqual(beautiful["CategoryCounts"]["Concerts & Music"], 50.0)
        self.assertEqual(beautiful["CategoryCounts"]["Theater & Drama"], 50.0)

        self.assertEqual(beautiful["SentimentCounts"]["Positive"], 50.0)
        self.assertEqual(beautiful["SentimentCounts"]["Neutral"], 50.0)
        self.assertEqual(beautiful["ArtistCounts"]["Harold Pinter"], 2)
        self.assertEqual(beautiful["ArtistCounts"]["Harriet Walter"], 1)
        self.assertIn("A beautiful line", beautiful["ConceptSnippets"])

        # Normalized per 100 records assertions
        self.assertEqual(beautiful["YearCountsNormalized"]["1995"], 100.0)
        self.assertEqual(beautiful["CategoryCountsRaw"]["Concerts & Music"], 1)
        self.assertEqual(beautiful["CategoryCountsNormalized"]["Concerts & Music"], 100.0)
        self.assertEqual(beautiful["SentimentCountsRaw"]["Positive"], 1)
        self.assertEqual(beautiful["SentimentCountsNormalized"]["Positive"], 100.0)


if __name__ == "__main__":
    unittest.main()

