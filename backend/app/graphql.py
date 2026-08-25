import asyncio
import math
import re
from typing import List, Optional
from bson import ObjectId
import strawberry

from .database import criticism_collection, word_collection
from .schema import (
    Criticism,
    CriticismSearchResult,
    FilterMetadata,
    ArtistPercentage,
    ConceptSnippet,
    WordCount,
    CountByArtist,
    CountByCategory,
    CountByYear,
    CountByConcept,
    CountBySentiment,
    SnippetsByArtist
)


PRIMARY_CATEGORIES = [
    "Theater & Drama",
    "Concerts & Music",
    "Art & Exhibitions",
    "Films & Cinema",
    "Opera",
    "Dance & Ballet",
    "Poetry & Literature",
    "Television & Radio",
    "Multiple / Other"
]

PRIMARY_SENTIMENTS = [
    "Positive",
    "Neutral",
    "Negative",
    "Mixed"
]


def map_to_primary_category(cat: str) -> str:
    """
    Map raw category string to one of the 9 Primary Canonical Categories.
    """
    if not cat:
        return "Multiple / Other"
    c = str(cat).strip().lower()
    if "theater" in c or "theatre" in c or "drama" in c or "play" in c:
        return "Theater & Drama"
    if "concert" in c or "music" in c or "rock" in c or "jazz" in c or "orchestra" in c or "band" in c or "cabaret" in c:
        return "Concerts & Music"
    if "art" in c or "exhibit" in c or "museum" in c or "gallery" in c or "sculpture" in c or "paint" in c:
        return "Art & Exhibitions"
    if "film" in c or "movie" in c or "cinema" in c:
        return "Films & Cinema"
    if "opera" in c or "operetta" in c:
        return "Opera"
    if "dance" in c or "ballet" in c:
        return "Dance & Ballet"
    if "poet" in c or "lit" in c or "book" in c or "novel" in c or "fiction" in c:
        return "Poetry & Literature"
    if "tv" in c or "tele" in c or "radio" in c or "broadcast" in c:
        return "Television & Radio"
    return "Multiple / Other"


def map_to_primary_sentiment(sent: str) -> str:
    """
    Map raw sentiment string to one of the 4 Primary Sentiments.
    """
    if not sent:
        return "Neutral"
    s = str(sent).strip().lower()
    if ("pos" in s and "neg" in s) or "mix" in s:
        return "Mixed"
    if "pos" in s:
        return "Positive"
    if "neg" in s:
        return "Negative"
    return "Neutral"


def map_category_to_regex(cat: str) -> str:
    """
    Map broad category groups to regex patterns matching raw DB categories.
    """
    c = cat.strip().lower()
    if "theater" in c or "drama" in c or "play" in c:
        return r"(theater|theatre|drama|play)"
    if "concert" in c or "music" in c:
        return r"(concert|music|rock|jazz|orchestra|band|cabaret)"
    if "art" in c or "exhibit" in c or "museum" in c or "gallery" in c:
        return r"(art|exhibit|museum|gallery|sculpture|paint)"
    if "film" in c or "cinema" in c or "movie" in c:
        return r"(film|movie|cinema)"
    if "opera" in c:
        return r"(opera|operetta)"
    if "dance" in c or "ballet" in c:
        return r"(dance|ballet)"
    if "poet" in c or "lit" in c or "book" in c:
        return r"(poet|literature|book|novel|fiction)"
    if "tv" in c or "tele" in c or "radio" in c:
        return r"(television|tv|radio|broadcast)"
    if "multiple" in c or "other" in c:
        return r"(multiple|various|unknown)"
    return re.escape(cat.strip())


def map_sentiment_to_regex(sent: str) -> str:
    """
    Map broad sentiment groups to regex patterns matching raw DB sentiments.
    """
    s = sent.strip().lower()
    if s == "positive":
        return r"^(positive|generally positive)$"
    if s == "neutral":
        return r"^(neutral|melancholic/neutral)$"
    if s == "negative":
        return r"^(negative|generally negative|melancholic/negative)$"
    if s == "mixed":
        return r"(mixed|positive.*negative|negative.*positive)"
    return re.escape(sent.strip())


def map_to_criticism(doc: dict) -> Criticism:
    """
    Map raw MongoDB criticism document to Criticism GraphQL type with safe fallbacks.
    """
    doc_id = str(doc.get("_id") or doc.get("Id") or doc.get("id") or "")
    author = doc.get("Author") or doc.get("author")
    title = doc.get("Title") or doc.get("title") or "Untitled"
    publication = doc.get("Publication") or doc.get("publication")

    # Dates
    date_val = doc.get("DateStr") or doc.get("Date") or doc.get("date")
    date_str = str(date_val) if date_val is not None else None
    date_epoch = doc.get("DateEpoch")
    if date_epoch is None and isinstance(doc.get("Date"), (int, float)):
        date_epoch = float(doc.get("Date"))

    year = doc.get("Year")
    if year is None and date_str:
        yr_match = re.search(r'\b(17|18|19|20)\d{2}\b', date_str)
        if yr_match:
            year = int(yr_match.group(0))

    place = doc.get("Place") or doc.get("place")
    full_text = doc.get("Full_text") or doc.get("full_text") or doc.get("text") or ""
    extracted_text = doc.get("extracted_text") or doc.get("Extracted_text") or ""
    url = doc.get("URL") or doc.get("url")
    category = doc.get("Category") or doc.get("category") or "Uncategorized"
    sentiment = doc.get("Sentiment") or doc.get("sentiment") or "Neutral"
    source = doc.get("Source") or doc.get("source") or "Gale"
    summary = doc.get("Summary") or doc.get("summary") or ""

    # Artist percentages
    artist_percentages = []
    raw_artists = doc.get("LLM_Artists_Percentages") or doc.get("artist_percentages") or {}
    if isinstance(raw_artists, dict):
        for artist_name, pct in raw_artists.items():
            if artist_name and str(artist_name).strip():
                try:
                    artist_percentages.append(
                        ArtistPercentage(artist=str(artist_name).strip(), percentage=float(pct))
                    )
                except (ValueError, TypeError):
                    artist_percentages.append(
                        ArtistPercentage(artist=str(artist_name).strip(), percentage=0.0)
                    )
    elif isinstance(raw_artists, list):
        for item in raw_artists:
            if isinstance(item, dict) and "artist" in item:
                artist_percentages.append(
                    ArtistPercentage(artist=str(item["artist"]), percentage=float(item.get("percentage", 0.0)))
                )

    # Found concepts
    raw_concepts = doc.get("Found_Concepts") or doc.get("found_concepts") or []
    found_concepts = [str(c).strip() for c in raw_concepts if c and str(c).strip()] if isinstance(raw_concepts, list) else []

    # Concept snippets
    concept_snippets = []
    raw_snippets = doc.get("Concept_Snippets") or doc.get("concept_snippets") or {}
    if isinstance(raw_snippets, dict):
        for concept_name, snips in raw_snippets.items():
            if concept_name and str(concept_name).strip():
                snippet_list = [str(s).strip() for s in snips if s and str(s).strip()] if isinstance(snips, list) else [str(snips).strip()]
                concept_snippets.append(
                    ConceptSnippet(concept=str(concept_name).strip(), snippets=snippet_list)
                )

    return Criticism(
        id=doc_id,
        author=str(author).strip() if author else None,
        title=str(title).strip() if title else "Untitled",
        publication=str(publication).strip() if publication else None,
        date=date_str,
        date_epoch=float(date_epoch) if date_epoch is not None else None,
        year=int(year) if year is not None else None,
        place=str(place).strip() if place else None,
        text=str(full_text),
        full_text=str(full_text),
        extracted_text=str(extracted_text),
        url=str(url) if url else None,
        category=str(category).strip(),
        sentiment=str(sentiment).strip(),
        source=str(source).strip(),
        summary=str(summary).strip(),
        artist_percentages=artist_percentages,
        found_concepts=found_concepts,
        concept_snippets=concept_snippets
    )


@strawberry.type
class Query:
    @strawberry.field
    async def criticism(self, id: str) -> Optional[Criticism]:
        query_conditions = [{"_id": id}, {"Id": id}]
        try:
            query_conditions.append({"_id": ObjectId(id)})
        except Exception:
            pass

        doc = await criticism_collection.find_one({"$or": query_conditions})
        if doc:
            return map_to_criticism(doc)
        return None

    @strawberry.field
    async def filter_metadata(self) -> FilterMetadata:
        try:
            total = await criticism_collection.estimated_document_count()
            return FilterMetadata(
                categories=PRIMARY_CATEGORIES,
                sentiments=PRIMARY_SENTIMENTS,
                total_criticisms=total
            )
        except Exception as e:
            print(f"Error fetching filter metadata: {e}")
            return FilterMetadata(categories=[], sentiments=[], total_criticisms=0)

    @strawberry.field
    async def search_criticisms(
        self,
        query: Optional[str] = None,
        artist: Optional[str] = None,
        author: Optional[str] = None,
        category: Optional[str] = None,
        sentiment: Optional[str] = None,
        concept: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> CriticismSearchResult:
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        filter_clauses = []

        if category and category.strip() and category.strip().lower() != "all":
            clean_cat = category.strip()
            if clean_cat in PRIMARY_CATEGORIES:
                filter_clauses.append({
                    "$or": [
                        {"PrimaryCategory": clean_cat},
                        {"Category": {"$regex": map_category_to_regex(clean_cat), "$options": "i"}}
                    ]
                })
            else:
                cat_regex = map_category_to_regex(clean_cat)
                filter_clauses.append({"Category": {"$regex": cat_regex, "$options": "i"}})

        if sentiment and sentiment.strip() and sentiment.strip().lower() != "all":
            clean_sent = sentiment.strip()
            if clean_sent in PRIMARY_SENTIMENTS:
                filter_clauses.append({
                    "$or": [
                        {"PrimarySentiment": clean_sent},
                        {"Sentiment": {"$regex": map_sentiment_to_regex(clean_sent), "$options": "i"}}
                    ]
                })
            else:
                sent_regex = map_sentiment_to_regex(clean_sent)
                filter_clauses.append({"Sentiment": {"$regex": sent_regex, "$options": "i"}})

        if author and author.strip():
            filter_clauses.append({"Author": {"$regex": f"^{re.escape(author.strip())}", "$options": "i"}})

        if artist and artist.strip():
            art_pattern = re.escape(artist.strip())
            filter_clauses.append({
                "$or": [
                    {"ArtistsList": {"$regex": art_pattern, "$options": "i"}},
                    {f"LLM_Artists_Percentages.{artist.strip()}": {"$exists": True}}
                ]
            })

        if concept and concept.strip():
            filter_clauses.append({
                "Found_Concepts": {"$regex": f"^{re.escape(concept.strip())}$", "$options": "i"}
            })

        if query and query.strip():
            q_clean = query.strip()
            filter_clauses.append({"$text": {"$search": q_clean}})

        mongo_filter = {"$and": filter_clauses} if filter_clauses else {}
        skip = (page - 1) * page_size

        # Fast parallel execution: count + find
        if not mongo_filter:
            count_task = criticism_collection.estimated_document_count()
        else:
            count_task = criticism_collection.count_documents(mongo_filter)

        find_task = (
            criticism_collection.find(mongo_filter)
            .sort([("DateEpoch", -1), ("_id", -1)])
            .skip(skip)
            .limit(page_size)
            .to_list(length=page_size)
        )

        total, raw_docs = await asyncio.gather(count_task, find_task)
        total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

        items = [map_to_criticism(d) for d in raw_docs]
        return CriticismSearchResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @strawberry.field
    async def criticisms(self) -> List[Criticism]:
        criticisms_list = await criticism_collection.find().limit(100).to_list(length=100)
        return [map_to_criticism(c) for c in criticisms_list]

    @strawberry.field
    async def total_count(self) -> int:
        return await criticism_collection.estimated_document_count()

    @strawberry.field
    async def word_counts(self, words: List[str]) -> List[WordCount]:
        cleaned_words = [w.strip().lower() for w in words if w and w.strip()]
        if not cleaned_words:
            return []

        cursor = word_collection.find({"Word": {"$in": cleaned_words}})
        results = await cursor.to_list(length=None)
        if not results:
            return []

        word_count_list = []
        for result in results:
            total_count = int(result.get("TotalCount", 0))

            year_counts = [
                CountByYear(year=int(yr) if str(yr).isdigit() else 0, count=float(count))
                for yr, count in (result.get("YearCounts") or {}).items()
            ]
            raw_category_counts = result.get("CategoryCounts") or {}
            canonical_category_counts = {cat: 0.0 for cat in PRIMARY_CATEGORIES}
            for cat, count in raw_category_counts.items():
                canonical_cat = map_to_primary_category(cat)
                canonical_category_counts[canonical_cat] = canonical_category_counts.get(canonical_cat, 0.0) + float(count)

            category_counts = [
                CountByCategory(category=cat, count=round(canonical_category_counts[cat], 2))
                for cat in PRIMARY_CATEGORIES
            ]

            raw_sentiment_counts = result.get("SentimentCounts") or {}
            canonical_sentiment_counts = {sent: 0.0 for sent in PRIMARY_SENTIMENTS}
            for sent, count in raw_sentiment_counts.items():
                s_lower = str(sent).strip().lower()
                if ("pos" in s_lower and "neg" in s_lower) or "mix" in s_lower:
                    canonical_sentiment_counts["Mixed"] += float(count)
                elif "pos" in s_lower:
                    canonical_sentiment_counts["Positive"] += float(count)
                elif "neg" in s_lower:
                    canonical_sentiment_counts["Negative"] += float(count)
                else:
                    canonical_sentiment_counts["Neutral"] += float(count)

            sentiment_counts = [
                CountBySentiment(sentiment=sent, count=round(canonical_sentiment_counts[sent], 2))
                for sent in PRIMARY_SENTIMENTS
            ]

            artist_counts = [
                CountByArtist(
                    artist=str(art),
                    count=float(count),
                    percentage=round((float(count) / total_count) * 100, 2) if total_count > 0 else 0.0
                )
                for art, count in (result.get("ArtistCounts") or {}).items()
            ]
            artist_snippets = [
                SnippetsByArtist(artist=str(art), snippets=snippets if isinstance(snippets, list) else [str(snippets)])
                for art, snippets in (result.get("ArtistSnippets") or {}).items()
            ]
            concept_counts = [
                CountByConcept(concept=str(c), count=float(count))
                for c, count in (result.get("ConceptCounts") or {}).items()
            ]

            raw_word_concept = result.get("WordConcept")
            word_concept_list = (
                raw_word_concept if isinstance(raw_word_concept, list) 
                else [str(raw_word_concept)] if raw_word_concept else []
            )

            raw_concept_snippets = result.get("ConceptSnippets") or []
            concept_snippets = [str(s) for s in raw_concept_snippets if s]

            word_count_list.append(WordCount(
                _id=str(result.get("_id") or result.get("Word", "")),
                Word=result.get("Word", ""),
                WordConcept=word_concept_list,
                TotalCount=total_count,
                YearCounts=year_counts,
                CategoryCounts=category_counts,
                ArtistCounts=artist_counts,
                ArtistSnippets=artist_snippets,
                ConceptCounts=concept_counts,
                SentimentCounts=sentiment_counts,
                ConceptSnippets=concept_snippets
            ))
        return word_count_list
