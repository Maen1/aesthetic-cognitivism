#!/usr/bin/env python3
"""
create_indexes.py
High-performance MongoDB index and canonical field backfill utility.
Optimizes query performance for low-resource servers (e.g., 2 vCPUs, 4GB RAM).
Runs in seconds on an existing database without re-ingesting raw data.
"""

import os
import sys
import time
from pymongo import MongoClient, UpdateOne, ASCENDING, DESCENDING, TEXT

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "aestheticv3")


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

    # 1. Check if PrimaryCategory / PrimarySentiment are backfilled
    sample = col.find_one({"PrimaryCategory": {"$exists": True}})
    if not sample and total_docs > 0:
        print("Backfilling PrimaryCategory and PrimarySentiment across documents...")
        t0 = time.time()
        batch = []
        updated = 0
        for doc in col.find({}, {"_id": 1, "Category": 1, "Sentiment": 1}):
            p_cat = map_to_primary_category(doc.get("Category"))
            p_sent = map_to_primary_sentiment(doc.get("Sentiment"))
            batch.append(UpdateOne({"_id": doc["_id"]}, {"$set": {"PrimaryCategory": p_cat, "PrimarySentiment": p_sent}}))
            if len(batch) >= 10000:
                col.bulk_write(batch, ordered=False)
                updated += len(batch)
                print(f"  Backfilled {updated:,} / {total_docs:,} records...")
                batch = []
        if batch:
            col.bulk_write(batch, ordered=False)
            updated += len(batch)
        print(f"✅ Backfill completed in {time.time() - t0:.2f}s ({updated:,} records updated).")
    else:
        print("✅ PrimaryCategory and PrimarySentiment fields are already present.")

    # 2. Build high performance compound indexes
    print("Building high-performance indexes (background=True)...")
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
