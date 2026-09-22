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
                "DateStr": "1995-07-29",
                "Publication": "The Times",
                "ArtistsList": ["Harold Pinter"],
                "Concept_Snippets": {"beautiful": ["A beautiful line"]}
            },
            {
                "Found_Concepts": ["beautiful"],
                "Category": "Theater",
                "Sentiment": "Neutral",
                "Year": 1995,
                "DateStr": "1995-08-15",
                "Publication": "The Guardian",
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
        self.assertEqual(len(beautiful["ConceptSnippets"]), 2)
        self.assertEqual(beautiful["ConceptSnippets"][0]["snippet"], "A beautiful line")
        self.assertEqual(beautiful["ConceptSnippets"][0]["publication"], "The Times")
        self.assertEqual(beautiful["ConceptSnippets"][0]["date"], "1995-07-29")
        self.assertEqual(beautiful["ConceptSnippets"][0]["year"], 1995)

        self.assertEqual(beautiful["ConceptSnippets"][0]["era"], "1980–2008")

        # Normalized per 100 records assertions
        self.assertEqual(beautiful["YearCountsNormalized"]["1995"], 100.0)
        self.assertEqual(beautiful["CategoryCountsRaw"]["Concerts & Music"], 1)
        self.assertEqual(beautiful["CategoryCountsNormalized"]["Concerts & Music"], 100.0)
        self.assertEqual(beautiful["SentimentCountsRaw"]["Positive"], 1)
        self.assertEqual(beautiful["SentimentCountsNormalized"]["Positive"], 100.0)

    def test_stratified_temporal_sampling(self):
        # Create documents spanning multiple historical eras
        era_test_docs = [
            # Era 1: 1785–1849
            {
                "Found_Concepts": ["sublime"],
                "Category": "Concerts",
                "Sentiment": "Positive",
                "Year": 1825,
                "DateStr": "1825-04-10",
                "Publication": "The Times",
                "ArtistsList": ["Beethoven"],
                "Concept_Snippets": {"sublime": ["A sublime symphony from 1825"]}
            },
            # Era 2: 1850–1899
            {
                "Found_Concepts": ["sublime"],
                "Category": "Opera",
                "Sentiment": "Positive",
                "Year": 1875,
                "DateStr": "1875-11-20",
                "Publication": "The Times",
                "ArtistsList": ["Wagner"],
                "Concept_Snippets": {"sublime": ["A sublime overture from 1875"]}
            },
            # Era 3: 1900–1949
            {
                "Found_Concepts": ["sublime"],
                "Category": "Theater",
                "Sentiment": "Neutral",
                "Year": 1928,
                "DateStr": "1928-02-15",
                "Publication": "The Guardian",
                "ArtistsList": ["Shaw"],
                "Concept_Snippets": {"sublime": ["A sublime drama from 1928"]}
            },
            # Era 4: 1950–1979
            {
                "Found_Concepts": ["sublime"],
                "Category": "Films",
                "Sentiment": "Positive",
                "Year": 1968,
                "DateStr": "1968-09-01",
                "Publication": "The Observer",
                "ArtistsList": ["Kubrick"],
                "Concept_Snippets": {"sublime": ["A sublime visual journey from 1968"]}
            },
            # Era 5: 1980–2008
            {
                "Found_Concepts": ["sublime"],
                "Category": "Concerts",
                "Sentiment": "Positive",
                "Year": 2002,
                "DateStr": "2002-06-18",
                "Publication": "The Independent",
                "ArtistsList": ["Radiohead"],
                "Concept_Snippets": {"sublime": ["A sublime performance from 2002"]}
            }
        ]

        results = aggregate_word_data(era_test_docs)
        sublime = next(r for r in results if r["Word"] == "sublime")
        snippets = sublime["ConceptSnippets"]

        self.assertEqual(len(snippets), 5)
        # Check chronological ordering
        years = [s["year"] for s in snippets]
        self.assertEqual(years, [1825, 1875, 1928, 1968, 2002])

        # Check era labels
        self.assertEqual(snippets[0]["era"], "1785–1849")
        self.assertEqual(snippets[1]["era"], "1850–1899")
        self.assertEqual(snippets[2]["era"], "1900–1949")
        self.assertEqual(snippets[3]["era"], "1950–1979")
        self.assertEqual(snippets[4]["era"], "1980–2008")


if __name__ == "__main__":
    unittest.main()

