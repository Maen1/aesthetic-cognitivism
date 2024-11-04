from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URL)
database = client["aesthetic"]
criticism_collection = database["criticism"]
word_collection = database["word_counts"]

