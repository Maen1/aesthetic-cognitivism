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

    # 2. Re-aggregate YearCounts for all concept words in word_counts
    print("Rebuilding timeline YearCounts across all concept words in 'word_counts'...")
    t0 = time.time()
    word_year_counts = defaultdict(lambda: defaultdict(int))
    for doc in col.find({}, {"_id": 1, "Found_Concepts": 1, "Year": 1}):
        yr = doc.get("Year")
        if yr is not None and 1700 <= yr <= 2050:
            yr_str = str(yr)
            for c in (doc.get("Found_Concepts") or []):
                word_year_counts[c][yr_str] += 1

    word_batch = []
    for word, y_counts in word_year_counts.items():
        word_batch.append(UpdateOne({"_id": word}, {"$set": {"YearCounts": dict(y_counts)}}))

    if word_batch:
        word_col.bulk_write(word_batch, ordered=False)
    print(f"✅ Rebuilt timeline YearCounts for {len(word_batch)} words in {time.time() - t0:.2f}s.")

    # 3. Build high performance compound indexes
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
