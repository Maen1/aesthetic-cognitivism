#!/usr/bin/env python3
"""
ingest_jsonl.py
Streaming JSONL ingestion and aggregation pipeline for Aesthetic Cognitivism.
Processes raw criticism JSONL datasets into MongoDB 'criticism' and 'word_counts' collections.
Designed for high throughput with constant low memory usage.
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime, timezone
from collections import defaultdict


def parse_date_info(raw_date):
    """
    Safely parse date into epoch ms (float), formatted ISO string, and integer year.
    Handles epoch ms integers/floats, ISO date strings, partial dates, and None.
    """
    if raw_date is None or raw_date == "" or str(raw_date).lower() == "nan":
        return None, None, None

    # Case 1: Numeric epoch (milliseconds)
    if isinstance(raw_date, (int, float)):
        try:
            # Check if timestamp in ms (> 1e11) or seconds (< 1e11)
            ts_sec = raw_date / 1000.0 if raw_date > 1e11 else float(raw_date)
            dt = datetime.fromtimestamp(ts_sec, tz=timezone.utc)
            return raw_date, dt.strftime("%Y-%m-%d"), dt.year
        except Exception:
            return raw_date, None, None

    # Case 2: String representations
    date_str = str(raw_date).strip()

    # Try parsing numeric string
    if date_str.isdigit():
        try:
            num = int(date_str)
            ts_sec = num / 1000.0 if num > 1e11 else float(num)
            dt = datetime.fromtimestamp(ts_sec, tz=timezone.utc)
            return num, dt.strftime("%Y-%m-%d"), dt.year
        except Exception:
            pass

    # Extract 4-digit year if present
    year = None
    yr_match = re.search(r'\b(17|18|19|20)\d{2}\b', date_str)
    if yr_match:
        year = int(yr_match.group(0))

    return None, date_str, year


def normalize_criticism_record(raw_dict):
    """
    Sanitize and normalize a single criticism JSONL record.
    Guarantees consistent keys and types across all records.
    """
    raw_id = raw_dict.get("Id") or raw_dict.get("_id") or raw_dict.get("id")
    doc_id = str(raw_id).strip() if raw_id else None

    author = raw_dict.get("Author")
    author_str = str(author).strip() if author and str(author).lower() not in {"nan", "none", "null"} else None

    title = raw_dict.get("Title")
    title_str = str(title).strip() if title and str(title).lower() not in {"nan", "none", "null"} else "Untitled"

    publication = raw_dict.get("Publication")
    pub_str = str(publication).strip() if publication and str(publication).lower() not in {"nan", "none", "null"} else None

    place = raw_dict.get("Place")
    place_str = str(place).strip() if place and str(place).lower() not in {"nan", "none", "null"} else None

    full_text = raw_dict.get("Full_text") or raw_dict.get("full_text") or ""
    extracted_text = raw_dict.get("extracted_text") or raw_dict.get("Extracted_text") or ""
    url = raw_dict.get("URL") or raw_dict.get("url") or None

    category = raw_dict.get("Category")
    cat_str = str(category).strip() if category and str(category).lower() not in {"nan", "none", "null"} else "Uncategorized"

    sentiment = raw_dict.get("Sentiment")
    sent_str = str(sentiment).strip().capitalize() if sentiment and str(sentiment).lower() not in {"nan", "none", "null"} else "Neutral"

    summary = raw_dict.get("Summary") or raw_dict.get("summary")
    sum_str = str(summary).strip() if summary and str(summary).lower() not in {"nan", "none", "null"} else ""

    # Artist percentages
    raw_artists = raw_dict.get("LLM_Artists_Percentages") or raw_dict.get("artist_percentages") or {}
    artist_percentages = {}
    if isinstance(raw_artists, dict):
        for k, v in raw_artists.items():
            if k and str(k).strip():
                try:
                    artist_percentages[str(k).strip()] = float(v)
                except (ValueError, TypeError):
                    artist_percentages[str(k).strip()] = 0.0

    artists_list = list(artist_percentages.keys())

    # Found concepts
    raw_concepts = raw_dict.get("Found_Concepts") or raw_dict.get("found_concepts") or []
    found_concepts = []
    if isinstance(raw_concepts, list):
        for c in raw_concepts:
            if c and str(c).strip():
                found_concepts.append(str(c).strip().lower())

    # Concept snippets
    raw_snippets = raw_dict.get("Concept_Snippets") or raw_dict.get("concept_snippets") or {}
    concept_snippets = {}
    if isinstance(raw_snippets, dict):
        for k, v in raw_snippets.items():
            k_clean = str(k).strip().lower()
            if isinstance(v, list):
                concept_snippets[k_clean] = [str(s).strip() for s in v if s and str(s).strip()]
            elif isinstance(v, str) and v.strip():
                concept_snippets[k_clean] = [v.strip()]

    # Dates
    date_epoch, date_str, year = parse_date_info(raw_dict.get("Date"))

    return {
        "_id": doc_id,
        "Id": doc_id,
        "Author": author_str,
        "Title": title_str,
        "Publication": pub_str,
        "Date": date_epoch if date_epoch is not None else date_str,
        "DateEpoch": date_epoch,
        "DateStr": date_str,
        "Year": year,
        "Place": place_str,
        "Full_text": str(full_text),
        "extracted_text": str(extracted_text),
        "URL": str(url) if url else None,
        "Category": cat_str,
        "Sentiment": sent_str,
        "Summary": sum_str,
        "LLM_Artists_Percentages": artist_percentages,
        "ArtistsList": artists_list,
        "Found_Concepts": found_concepts,
        "Concept_Snippets": concept_snippets
    }


def aggregate_word_data(documents):
    """
    Compute pre-aggregated statistics for the word_counts collection from a list of documents.
    """
    total_counts = defaultdict(int)
    year_counts = defaultdict(lambda: defaultdict(int))
    category_counts = defaultdict(lambda: defaultdict(int))
    sentiment_counts = defaultdict(lambda: defaultdict(int))
    artist_counts = defaultdict(lambda: defaultdict(int))
    artist_snippets = defaultdict(lambda: defaultdict(list))
    concept_snippets_agg = defaultdict(list)

    for doc in documents:
        update_word_aggregates(
            doc,
            total_counts,
            year_counts,
            category_counts,
            sentiment_counts,
            artist_counts,
            artist_snippets,
            concept_snippets_agg
        )

    return build_word_count_records(
        total_counts,
        year_counts,
        category_counts,
        sentiment_counts,
        artist_counts,
        artist_snippets,
        concept_snippets_agg
    )


def map_to_primary_category(cat: str) -> str:
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


def update_word_aggregates(doc, total_counts, year_counts, category_counts, sentiment_counts, artist_counts, artist_snippets, concept_snippets_agg):
    """
    Update running aggregation dictionaries for a single document.
    """
    concepts = doc.get("Found_Concepts") or []
    raw_cat = doc.get("Category", "Uncategorized")
    doc_category = map_to_primary_category(raw_cat)
    sentiment = doc.get("Sentiment", "Neutral")
    year_val = str(doc.get("Year") or "Unknown")
    artists = doc.get("ArtistsList") or []
    snippets_dict = doc.get("Concept_Snippets") or {}

    for word in concepts:
        total_counts[word] += 1
        year_counts[word][year_val] += 1
        category_counts[word][doc_category] += 1
        sentiment_counts[word][sentiment] += 1


        for artist in artists:
            artist_counts[word][artist] += 1

        word_snippets = snippets_dict.get(word, [])
        if word_snippets:
            if len(concept_snippets_agg[word]) < 50:
                concept_snippets_agg[word].extend(word_snippets[:3])

            for artist in artists:
                if len(artist_snippets[word][artist]) < 15:
                    artist_snippets[word][artist].extend(word_snippets[:2])


def build_word_count_records(total_counts, year_counts, category_counts, sentiment_counts, artist_counts, artist_snippets, concept_snippets_agg):
    """
    Format running aggregation dictionaries into MongoDB word_count documents.
    Safely limits top artists and snippets to avoid BSON document size limits.
    """
    results = []
    for word, total in total_counts.items():
        if total == 0:
            continue

        def to_percent(d, count_total):
            return {k: round((v / count_total) * 100, 2) for k, v in d.items()}

        # Keep top 300 artists by mention count
        sorted_artists = sorted(artist_counts[word].items(), key=lambda x: x[1], reverse=True)
        top_artists_dict = dict(sorted_artists[:300])
        top_artist_names = set(top_artists_dict.keys())

        # Keep snippets only for top artists (max 3 snippets each)
        pruned_snippets = {}
        for artist in top_artists_dict:
            if artist in artist_snippets[word]:
                unique_snips = list(dict.fromkeys(artist_snippets[word][artist]))[:3]
                if unique_snips:
                    pruned_snippets[artist] = unique_snips

        results.append({
            "_id": word,
            "Word": word,
            "TotalCount": total,
            "YearCounts": dict(year_counts[word]),
            "CategoryCounts": to_percent(category_counts[word], total),
            "SentimentCounts": to_percent(sentiment_counts[word], total),
            "ArtistCounts": top_artists_dict,
            "ArtistSnippets": pruned_snippets,
            "ConceptSnippets": list(dict.fromkeys(concept_snippets_agg[word]))[:50]
        })
    return results



def ingest_file(input_file, mongo_uri="mongodb://localhost:27017", db_name="aestheticv3", batch_size=5000, drop_first=False):
    """
    Stream and ingest JSONL file into MongoDB with constant low memory usage.
    """
    try:
        from pymongo import MongoClient, ReplaceOne, ASCENDING, DESCENDING, TEXT
    except ImportError:
        raise ImportError("pymongo is required to run database ingestion. Install with: pip install pymongo")

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    print(f"Connecting to MongoDB at {mongo_uri}, database: {db_name}...")
    client = MongoClient(mongo_uri)
    db = client[db_name]
    criticism_col = db["criticism"]
    word_col = db["word_counts"]

    if drop_first:
        print("Dropping existing collections...")
        criticism_col.drop()
        word_col.drop()

    print(f"Streaming JSONL file: {input_file} (batch size: {batch_size})...")
    criticism_batch = []
    total_records = 0

    # Running aggregation state
    total_counts = defaultdict(int)
    year_counts = defaultdict(lambda: defaultdict(int))
    category_counts = defaultdict(lambda: defaultdict(int))
    sentiment_counts = defaultdict(lambda: defaultdict(int))
    artist_counts = defaultdict(lambda: defaultdict(int))
    artist_snippets = defaultdict(lambda: defaultdict(list))
    concept_snippets_agg = defaultdict(list)

    with open(input_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                raw_record = json.loads(line)
                normalized = normalize_criticism_record(raw_record)
                if not normalized.get("_id"):
                    normalized["_id"] = f"doc_{line_num}"
                    normalized["Id"] = normalized["_id"]

                criticism_batch.append(
                    ReplaceOne({"_id": normalized["_id"]}, normalized, upsert=True)
                )

                # Update on-the-fly aggregation
                update_word_aggregates(
                    normalized,
                    total_counts,
                    year_counts,
                    category_counts,
                    sentiment_counts,
                    artist_counts,
                    artist_snippets,
                    concept_snippets_agg
                )

                total_records += 1

                if len(criticism_batch) >= batch_size:
                    criticism_col.bulk_write(criticism_batch, ordered=False)
                    criticism_batch = []
                    print(f"  Processed {total_records} criticism records...")
            except Exception as e:
                print(f"⚠️ Error on line {line_num}: {e}", file=sys.stderr)

    if criticism_batch:
        criticism_col.bulk_write(criticism_batch, ordered=False)
        print(f"  Processed final batch ({total_records} total criticism records).")

    print("Building pre-aggregated word statistics...")
    word_aggregates = build_word_count_records(
        total_counts,
        year_counts,
        category_counts,
        sentiment_counts,
        artist_counts,
        artist_snippets,
        concept_snippets_agg
    )
    print(f"Inserting/updating {len(word_aggregates)} concept word records into 'word_counts'...")
    if word_aggregates:
        word_col.delete_many({})
        word_col.insert_many(word_aggregates)

    print("Building MongoDB indexes...")
    criticism_col.create_index([("Category", ASCENDING), ("Sentiment", ASCENDING), ("DateEpoch", DESCENDING)])
    criticism_col.create_index([("Found_Concepts", ASCENDING)])
    criticism_col.create_index([("ArtistsList", ASCENDING)])
    criticism_col.create_index([("Author", ASCENDING)])
    criticism_col.create_index([("Year", ASCENDING)])
    criticism_col.create_index([
        ("Title", TEXT),
        ("Summary", TEXT),
        ("Full_text", TEXT),
        ("Author", TEXT)
    ], name="criticism_text_search")

    word_col.create_index([("Word", ASCENDING)], unique=True)


    print(f"✅ Ingestion complete! {total_records} criticisms and {len(word_aggregates)} words stored.")
    return total_records, len(word_aggregates)


def main():
    parser = argparse.ArgumentParser(description="Ingest JSONL dataset for Aesthetic Cognitivism into MongoDB.")
    parser.add_argument("--input", "-i", required=True, help="Path to input .jsonl file")
    parser.add_argument("--mongo-uri", default=os.getenv("MONGO_URL", "mongodb://localhost:27017"), help="MongoDB connection URI")
    parser.add_argument("--db", default="aestheticv3", help="MongoDB database name")
    parser.add_argument("--batch-size", type=int, default=5000, help="Batch size for bulk operations")
    parser.add_argument("--drop", action="store_true", help="Drop existing collections before ingestion")

    args = parser.parse_args()
    ingest_file(
        input_file=args.input,
        mongo_uri=args.mongo_uri,
        db_name=args.db,
        batch_size=args.batch_size,
        drop_first=args.drop
    )


if __name__ == "__main__":
    main()
