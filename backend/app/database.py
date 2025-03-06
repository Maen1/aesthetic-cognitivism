from motor.motor_asyncio import AsyncIOMotorClient

# MONGO_URL = "mongodb://localhost:27017"
# MONGO_URL = "mongodb://host.docker.internal:27017"
MONGO_URL = "mongodb://mongodb:27017"
client = AsyncIOMotorClient(MONGO_URL)
database = client["aesthetic"]
criticism_collection = database["criticism"]
word_collection = database["word_counts"]