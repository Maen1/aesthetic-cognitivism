from transformers import pipeline
import spacy
from pymongo import MongoClient

MONGO_URL = "mongodb://localhost:27017"
client = MongoClient(MONGO_URL)
database = client["aesthetic"]
criticism_collection = database["criticism"]
word_collection = database["word_counts"]

print(criticism_collection.findall())

ner_pipeline = pipeline("ner", grouped_entities=True)
text = "adam maen works at cdhu, on aesthetic project owned by guy dammann."

entities = ner_pipeline(text)
# Filter for PERSON entities
names = [entity["word"] for entity in entities if entity["entity_group"] == "PER"]
print("Ner found:", names)


# Load the pre-trained English model
nlp = spacy.load("en_core_web_sm")


# Process the text
doc = nlp(text)

# Extract names (PERSON entities)
names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]

print("Spacy found:", names)
print("spacy is way faster and better than ner")
