import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
database = client["aestheticv3"]
criticism_collection = database["criticism"]
word_collection = database["word_counts"]
corpus_metadata_collection = database["corpus_metadata"]
