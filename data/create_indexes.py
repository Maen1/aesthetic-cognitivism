#!/usr/bin/env python3
"""
create_indexes.py
High-performance MongoDB index, canonical category/sentiment backfill,
and historical date repair utility for Aesthetic Cognitivism.
Optimizes query performance and fixes Year timeline values on low-resource servers (e.g. 2 vCPUs, 4GB RAM).
Runs in ~20-30 seconds on an existing database without re-ingesting raw data.
"""

import os
import sys
import time
import re
from datetime import datetime, timezone
from collections import defaultdict
from pymongo import MongoClient, UpdateOne, ASCENDING, DESCENDING, TEXT

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "aestheticv3")


def parse_date_info(raw_date):
    """
    Safely parse date into epoch ms (float), formatted ISO string, and integer year.
    All numeric timestamps in Gale archive datasets are in milliseconds.
    """
    if raw_date is None or raw_date == "" or str(raw_date).lower() == "nan":
        return None, None, None

    # Case 1: Numeric epoch (milliseconds)
    if isinstance(raw_date, (int, float)):
        try:
            val = float(raw_date)
            ts_sec = val / 1000.0
            dt = datetime.fromtimestamp(ts_sec, tz=timezone.utc)
            return int(val), dt.strftime("%Y-%m-%d"), dt.year
        except Exception:
            return raw_date, None, None

    # Case 2: Numeric string
    date_str = str(raw_date).strip()
    if date_str.lstrip('-').replace('.', '', 1).isdigit():
        try:
            val = float(date_str)
            ts_sec = val / 1000.0
            dt = datetime.fromtimestamp(ts_sec, tz=timezone.utc)
            return int(val), dt.strftime("%Y-%m-%d"), dt.year
        except Exception:
            pass

    # Case 3: 4-digit year pattern
    year = None
    yr_match = re.search(r'\b(17|18|19|20)\d{2}\b', date_str)
    if yr_match:
        year = int(yr_match.group(0))

    return None, date_str, year


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


def map_to_primary_sentiment(sent: str) -> str:
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


def optimize_database(mongo_url=MONGO_URL, db_name=DB_NAME):
    print(f"Connecting to MongoDB at {mongo_url}, database: {db_name}...")
    client = MongoClient(mongo_url)
    db = client[db_name]
    col = db["criticism"]
    word_col = db["word_counts"]

    total_docs = col.estimated_document_count()
    print(f"Found {total_docs:,} criticism records.")

    # 1. Backfill and Repair Date / Canonical Fields in Criticism
    print("Verifying and repairing Date, PrimaryCategory, and PrimarySentiment fields...")
    t0 = time.time()
    batch = []
    updated = 0
    for doc in col.find({}, {"_id": 1, "Date": 1, "Category": 1, "Sentiment": 1}):
        epoch, dt_str, yr = parse_date_info(doc.get("Date"))
        p_cat = map_to_primary_category(doc.get("Category"))
        p_sent = map_to_primary_sentiment(doc.get("Sentiment"))
        
        batch.append(UpdateOne(
            {"_id": doc["_id"]},
            {"$set": {
                "DateEpoch": epoch,
                "DateStr": dt_str,
                "Year": yr,
                "PrimaryCategory": p_cat,
                "PrimarySentiment": p_sent
            }}
        ))
        if len(batch) >= 10000:
            col.bulk_write(batch, ordered=False)
            updated += len(batch)
            print(f"  Processed {updated:,} / {total_docs:,} records...")
            batch = []
    if batch:
        col.bulk_write(batch, ordered=False)
        updated += len(batch)
    print(f"✅ Repaired & backfilled {updated:,} records in {time.time() - t0:.2f}s.")

    # 2. Re-aggregate Year, Category, and Sentiment counts (both Raw and Normalized per 100 records)
    print("Rebuilding timeline, category, and sentiment counts across all concept words in 'word_counts'...")
    t0 = time.time()
    meta_col = db["corpus_metadata"]

    corpus_years = defaultdict(int)
    corpus_categories = defaultdict(int)
    corpus_sentiments = defaultdict(int)

    word_year_counts = defaultdict(lambda: defaultdict(int))
    word_cat_counts = defaultdict(lambda: defaultdict(int))
    word_sent_counts = defaultdict(lambda: defaultdict(int))

    for doc in col.find({}, {"_id": 1, "Found_Concepts": 1, "Year": 1, "PrimaryCategory": 1, "PrimarySentiment": 1}):
        yr = doc.get("Year")
        cat = doc.get("PrimaryCategory")
        sent = doc.get("PrimarySentiment")

        if yr is not None and 1700 <= yr <= 2050:
            corpus_years[str(yr)] += 1
        if cat:
            corpus_categories[cat] += 1
        if sent:
            corpus_sentiments[sent] += 1

        concepts = doc.get("Found_Concepts") or []
        for c in concepts:
            if yr is not None and 1700 <= yr <= 2050:
                word_year_counts[c][str(yr)] += 1
            if cat:
                word_cat_counts[c][cat] += 1
            if sent:
                word_sent_counts[c][sent] += 1

    # Save corpus metadata totals
    meta_col.replace_one(
        {"_id": "corpus_totals"},
        {
            "_id": "corpus_totals",
            "total_criticisms": total_docs,
            "records_by_year": dict(corpus_years),
            "records_by_category": dict(corpus_categories),
            "records_by_sentiment": dict(corpus_sentiments),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        upsert=True
    )
    print(f"✅ Saved corpus baseline totals ({len(corpus_years)} years, {len(corpus_categories)} categories, {len(corpus_sentiments)} sentiments) to 'corpus_metadata'.")

    all_words = set(list(word_year_counts.keys()) + list(word_cat_counts.keys()))
    word_batch = []
    for word in all_words:
        y_raw = dict(word_year_counts[word])
        y_norm = {
            yr: round((cnt / corpus_years[yr]) * 100, 3)
            for yr, cnt in y_raw.items() if corpus_years.get(yr, 0) > 0
        }

        c_raw = dict(word_cat_counts[word])
        c_norm = {
            cat: round((cnt / corpus_categories[cat]) * 100, 3)
            for cat, cnt in c_raw.items() if corpus_categories.get(cat, 0) > 0
        }

        s_raw = dict(word_sent_counts[word])
        s_norm = {
            sent: round((cnt / corpus_sentiments[sent]) * 100, 3)
            for sent, cnt in s_raw.items() if corpus_sentiments.get(sent, 0) > 0
        }

        word_batch.append(UpdateOne(
            {"_id": word},
            {"$set": {
                "YearCounts": y_raw,
                "YearCountsNormalized": y_norm,
                "CategoryCountsRaw": c_raw,
                "CategoryCountsNormalized": c_norm,
                "SentimentCountsRaw": s_raw,
                "SentimentCountsNormalized": s_norm
            }}
        ))

    if word_batch:
        word_col.bulk_write(word_batch, ordered=False)
    print(f"✅ Rebuilt raw and normalized statistics for {len(word_batch)} words in {time.time() - t0:.2f}s.")

    # 3. Enrich ConceptSnippets with publication, date, year, title, author metadata
    print("Enriching ConceptSnippets with publication and date metadata in 'word_counts'...")
    t0 = time.time()
    snippet_batch = []
    words_in_db = [doc["_id"] for doc in word_col.find({}, {"_id": 1})]
    for word in words_in_db:
        cursor = col.find(
            {"Found_Concepts": word},
            {
                f"Concept_Snippets.{word}": 1,
                "Publication": 1,
                "DateStr": 1,
                "Year": 1,
                "Title": 1,
                "Author": 1
            }
        ).limit(100)

        seen_snips = set()
        enriched_snippets = []
        for cdoc in cursor:
            snips = (cdoc.get("Concept_Snippets") or {}).get(word, [])
            pub = cdoc.get("Publication")
            dt = cdoc.get("DateStr") or (str(cdoc.get("Year")) if cdoc.get("Year") else None)
            yr = cdoc.get("Year")
            title = cdoc.get("Title") if cdoc.get("Title") and cdoc.get("Title") != "Untitled" else None
            author = cdoc.get("Author")

            for s in snips:
                if s and s not in seen_snips:
                    seen_snips.add(s)
                    enriched_snippets.append({
                        "snippet": s,
                        "publication": pub,
                        "date": dt,
                        "year": yr,
                        "title": title,
                        "author": author
                    })
                    if len(enriched_snippets) >= 50:
                        break
            if len(enriched_snippets) >= 50:
                break

        if enriched_snippets:
            snippet_batch.append(UpdateOne(
                {"_id": word},
                {"$set": {"ConceptSnippets": enriched_snippets}}
            ))

    if snippet_batch:
        word_col.bulk_write(snippet_batch, ordered=False)
    print(f"✅ Enriched ConceptSnippets with metadata for {len(snippet_batch)} words in {time.time() - t0:.2f}s.")

    # 4. Build high performance compound indexes
    print("Building high-performance compound indexes (background=True)...")
    t0 = time.time()

    indexes = [
        ([("DateEpoch", DESCENDING), ("_id", DESCENDING)], {}),
        ([("PrimaryCategory", ASCENDING), ("DateEpoch", DESCENDING)], {}),
        ([("PrimaryCategory", ASCENDING), ("PrimarySentiment", ASCENDING), ("DateEpoch", DESCENDING)], {}),
        ([("PrimarySentiment", ASCENDING), ("DateEpoch", DESCENDING)], {}),
        ([("Found_Concepts", ASCENDING), ("DateEpoch", DESCENDING)], {}),
        ([("ArtistsList", ASCENDING), ("DateEpoch", DESCENDING)], {}),
        ([("Author", ASCENDING), ("DateEpoch", DESCENDING)], {}),
        ([("Year", ASCENDING), ("DateEpoch", DESCENDING)], {}),
        ([
            ("Title", TEXT),
            ("Summary", TEXT),
            ("Full_text", TEXT),
            ("Author", TEXT)
        ], {"name": "criticism_text_search"})
    ]

    for keys, kwargs in indexes:
        col.create_index(keys, **kwargs)

    word_col.create_index([("Word", ASCENDING)], unique=True)

    print(f"✅ All indexes created successfully in {time.time() - t0:.2f}s!")
    print("\nActive indexes on 'criticism':")
    for idx in col.list_indexes():
        print(f"  - {idx['name']}: {dict(idx['key'])}")


if __name__ == "__main__":
    optimize_database()
