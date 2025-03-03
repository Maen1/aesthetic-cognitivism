from transformers import pipeline

# Load the NER pipeline
ner_pipeline = pipeline("ner", grouped_entities=True)

# Input text
text = "adam maen works at cdhu, on aesthetic project owned by guy dammann."

# Extract entities
entities = ner_pipeline(text)

# Filter for PERSON entities
names = [entity["word"] for entity in entities if entity["entity_group"] == "PER"]

print("Ner found:", names)


import spacy

# Load the pre-trained English model
nlp = spacy.load("en_core_web_sm")


# Process the text
doc = nlp(text)

# Extract names (PERSON entities)
names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]

print("Spacy found:", names)
print("spacy is way faster and better than ner")
