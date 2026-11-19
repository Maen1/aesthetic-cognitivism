import os
import re
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, TEXT, ReplaceOne

logger = logging.getLogger("aesthetic.database")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
database = client["aestheticv3"]
criticism_collection = database["criticism"]
word_collection = database["word_counts"]
corpus_metadata_collection = database["corpus_metadata"]
artists_index_collection = database["artists_index"]

CRITICISM_INDEXES = [
    ([("DateEpoch", DESCENDING), ("_id", DESCENDING)], {}),
    ([("PrimaryCategory", ASCENDING), ("DateEpoch", DESCENDING)], {}),
    ([("PrimaryCategory", ASCENDING), ("PrimarySentiment", ASCENDING), ("DateEpoch", DESCENDING)], {}),
    ([("PrimarySentiment", ASCENDING), ("DateEpoch", DESCENDING)], {}),
    ([("Found_Concepts", ASCENDING), ("DateEpoch", DESCENDING)], {}),
    ([("Found_Concepts", ASCENDING), ("PrimaryCategory", ASCENDING)], {}),
    ([("ArtistsList", ASCENDING), ("DateEpoch", DESCENDING)], {}),
    ([("Author", ASCENDING), ("DateEpoch", DESCENDING)], {}),
    ([("Title", ASCENDING), ("DateEpoch", DESCENDING)], {}),
    ([("Year", ASCENDING), ("DateEpoch", DESCENDING)], {}),
    ([
        ("Title", TEXT),
        ("Summary", TEXT),
        ("Full_text", TEXT),
        ("Author", TEXT)
    ], {"name": "criticism_text_search"})
]


def tokenize_artist_name(name: str) -> list[str]:
    """Extract unique lowercase word tokens from an artist name for fast prefix/token lookup."""
    if not name:
        return []
    return list(dict.fromkeys(re.findall(r"\w+", str(name).lower())))


async def ensure_artists_index(force_rebuild: bool = False):
    """
    Build and index the compact artists_index directory collection for sub-50ms partial artist queries.
    """
    try:
        await artists_index_collection.create_index(
            [("tokens", ASCENDING), ("count", DESCENDING)], background=True
        )
        await artists_index_collection.create_index([("count", DESCENDING)], background=True)

        if not force_rebuild:
            existing_count = await artists_index_collection.estimated_document_count()
            if existing_count > 0:
                return

        crit_count = await criticism_collection.estimated_document_count()
        if crit_count == 0:
            return

        logger.info("Building artists_index directory from criticism collection...")
        pipeline = [
            {"$match": {"ArtistsList": {"$exists": True, "$ne": []}}},
            {"$project": {"ArtistsList": 1}},
            {"$unwind": "$ArtistsList"},
            {"$group": {"_id": "$ArtistsList", "count": {"$sum": 1}}},
        ]
        docs = await criticism_collection.aggregate(pipeline).to_list(length=None)
        if not docs:
            return

        ops = []
        for d in docs:
            name = str(d["_id"]).strip()
            if not name:
                continue
            ops.append(
                ReplaceOne(
                    {"_id": name},
                    {
                        "_id": name,
                        "lower": name.lower(),
                        "tokens": tokenize_artist_name(name),
                        "count": int(d["count"]),
                    },
                    upsert=True,
                )
            )
            if len(ops) >= 10000:
                await artists_index_collection.bulk_write(ops, ordered=False)
                ops = []
        if ops:
            await artists_index_collection.bulk_write(ops, ordered=False)

        logger.info(f"Built artists_index directory with {len(docs)} artists.")
    except Exception as e:
        logger.warning(f"Could not ensure artists_index: {e}")


async def ensure_indexes():
    """
    Ensure required compound and full-text indexes exist on the criticism collection.
    Runs idempotently in background.
    """
    try:
        existing = await criticism_collection.index_information()
        existing_names = set(existing.keys())
        for keys, kwargs in CRITICISM_INDEXES:
            idx_name = kwargs.get("name")
            if idx_name and idx_name in existing_names:
                continue
            await criticism_collection.create_index(keys, background=True, **kwargs)
        await ensure_artists_index(force_rebuild=False)
        logger.info("MongoDB indexes verified.")
    except Exception as e:
        logger.warning(f"Could not automatically ensure indexes: {e}")

