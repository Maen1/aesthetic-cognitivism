import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, TEXT

logger = logging.getLogger("aesthetic.database")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
database = client["aestheticv3"]
criticism_collection = database["criticism"]
word_collection = database["word_counts"]
corpus_metadata_collection = database["corpus_metadata"]

CRITICISM_INDEXES = [
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
        logger.info("MongoDB indexes verified.")
    except Exception as e:
        logger.warning(f"Could not automatically ensure indexes: {e}")

