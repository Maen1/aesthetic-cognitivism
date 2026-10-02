import sys
import os
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schema import Criticism, WordCount, ArtistPercentage, ConceptSnippet, ContextSnippet
from app.graphql import map_to_criticism, Query
import strawberry


class TestGraphQLSchema(unittest.TestCase):

    def test_schema_compilation(self):
        schema = strawberry.Schema(query=Query)
        sdl = str(schema)
        self.assertIn("searchCriticisms", sdl)
        self.assertIn("filterMetadata", sdl)
        self.assertIn("wordCounts", sdl)
        self.assertIn("ArtistPercentage", sdl)
        self.assertIn("ConceptSnippet", sdl)
        self.assertIn("ContextSnippet", sdl)
        self.assertIn("normalizedCount", sdl)
        self.assertIn("rawCount", sdl)
        self.assertIn("totalRecords", sdl)
        self.assertIn("publication", sdl)
        self.assertIn("date", sdl)
        self.assertIn("era", sdl)

    def test_schema_has_year_filter_fields(self):
        schema = strawberry.Schema(query=Query)
        sdl = str(schema)
        self.assertIn("startYear: Int", sdl)
        self.assertIn("endYear: Int", sdl)
        self.assertIn("minYear: Int", sdl)
        self.assertIn("maxYear: Int", sdl)
        self.assertIn("sortBy: String", sdl)

    def test_graphql_queries_with_year_filter(self):
        async def run_queries():
            schema = strawberry.Schema(query=Query)
            meta_res = await schema.execute("""
                query {
                    filterMetadata {
                        minYear
                        maxYear
                        categories
                        sentiments
                    }
                }
            """)
            self.assertIsNone(meta_res.errors)
            self.assertIsNotNone(meta_res.data)
            self.assertIn("minYear", meta_res.data["filterMetadata"])
            self.assertIn("maxYear", meta_res.data["filterMetadata"])
            self.assertGreaterEqual(meta_res.data["filterMetadata"]["maxYear"], meta_res.data["filterMetadata"]["minYear"])

            search_res = await schema.execute("""
                query {
                    searchCriticisms(startYear: 1800, endYear: 1850, sortBy: "date_asc", pageSize: 5) {
                        total
                        page
                        pageSize
                        items {
                            id
                            year
                        }
                    }
                }
            """)
            self.assertIsNone(search_res.errors)
            self.assertIsNotNone(search_res.data)
            items = search_res.data["searchCriticisms"]["items"]
            self.assertTrue(len(items) > 0)
            years = [it["year"] for it in items if it["year"] is not None]
            for yr in years:
                self.assertGreaterEqual(yr, 1800)
                self.assertLessEqual(yr, 1850)
            # Verify ascending order
            self.assertEqual(years, sorted(years))

        import asyncio
        asyncio.run(run_queries())





    def test_map_to_criticism_full(self):
        doc = {
            "_id": "test_1",
            "Author": "Brown, Geoff",
            "Title": "Casper Review",
            "Publication": "The Times",
            "Date": "1995-07-29",
            "DateEpoch": 806976000000.0,
            "Year": 1995,
            "Place": "London",
            "Full_text": "Casper the ghost review...",
            "extracted_text": "Extracted text...",
            "URL": "https://link.gale.com/test",
            "Category": "Films",
            "Sentiment": "Positive",
            "Summary": "A delightful film overview",
            "LLM_Artists_Percentages": {"Christina Ricci": 5.0, "Bill Pullman": 3.0},
            "Found_Concepts": ["delighted", "emotional"],
            "Concept_Snippets": {
                "delighted": ["Snippet of delighted"],
                "emotional": ["Snippet of emotional"]
            }
        }
        item = map_to_criticism(doc)
        self.assertEqual(item.id, "test_1")
        self.assertEqual(item.author, "Brown, Geoff")
        self.assertEqual(item.title, "Casper Review")
        self.assertEqual(item.date, "1995-07-29")
        self.assertEqual(item.date_epoch, 806976000000.0)
        self.assertEqual(item.year, 1995)
        self.assertEqual(item.summary, "A delightful film overview")
        self.assertEqual(len(item.artist_percentages), 2)
        self.assertEqual(item.artist_percentages[0].artist, "Christina Ricci")
        self.assertEqual(item.artist_percentages[0].percentage, 5.0)
        self.assertEqual(item.found_concepts, ["delighted", "emotional"])
        self.assertEqual(len(item.concept_snippets), 2)
        self.assertEqual(item.concept_snippets[0].concept, "delighted")
        self.assertEqual(item.concept_snippets[0].snippets, ["Snippet of delighted"])

    def test_map_to_criticism_empty_and_nulls(self):
        doc = {
            "_id": "empty_doc",
            "Author": None,
            "Title": None,
            "Date": None,
            "LLM_Artists_Percentages": None,
            "Found_Concepts": None,
            "Concept_Snippets": None
        }
        item = map_to_criticism(doc)
        self.assertEqual(item.id, "empty_doc")
        self.assertIsNone(item.author)
        self.assertEqual(item.title, "Untitled")
        self.assertEqual(item.category, "Uncategorized")
        self.assertEqual(item.sentiment, "Neutral")
    def test_context_snippet_resolution(self):
        dict_snippet = {
            "snippet": "A sublime passage",
            "publication": "The Times",
            "date": "1995-07-29",
            "year": 1995,
            "title": "Theatre",
            "author": "Marlowe, Sam"
        }
        legacy_snippet = "Legacy string snippet"

        cs_dict = ContextSnippet(
            snippet=dict_snippet["snippet"],
            publication=dict_snippet["publication"],
            date=dict_snippet["date"],
            year=dict_snippet["year"],
            title=dict_snippet["title"],
            author=dict_snippet["author"],
            era="1980–2008"
        )
        cs_legacy = ContextSnippet(snippet=legacy_snippet)

        self.assertEqual(cs_dict.snippet, "A sublime passage")
        self.assertEqual(cs_dict.publication, "The Times")
        self.assertEqual(cs_dict.date, "1995-07-29")
        self.assertEqual(cs_dict.year, 1995)
        self.assertEqual(cs_dict.title, "Theatre")
        self.assertEqual(cs_dict.author, "Marlowe, Sam")
        self.assertEqual(cs_dict.era, "1980–2008")

        self.assertEqual(cs_legacy.snippet, "Legacy string snippet")
        self.assertIsNone(cs_legacy.publication)
        self.assertIsNone(cs_legacy.date)
        self.assertIsNone(cs_legacy.era)


if __name__ == "__main__":
    unittest.main()
