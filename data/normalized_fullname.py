import pandas as pd
import re
from collections import defaultdict
import ast
from pymongo import MongoClient

# ---------------------------
# Configuration
# ---------------------------
INPUT_CSV = "filtered_with_concepts_and_artists_clean_90.csv"
CHUNK_SIZE = 20000
ARTIST_XLSX = "top_1000_artists_critiqued.xlsx"

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "aestheticv3"
RESULT_COLLECTION = "word_counts"

CONCEPT_CSV = "concepts.csv"
MAX_SNIPPET_LEN = 300

# ---------------------------
# Load artist mapping: surname (from "Surname for index") → full name = First + Last
# ---------------------------
print("Loading artist metadata and building surname → full-name map...")
artist_df = pd.read_excel(ARTIST_XLSX, usecols=["Surname for index", "Other names"])
artist_df = artist_df.dropna(subset=["Surname for index"])

artist_name_map = {}  # key: surname (lowercase), value: "First Last" or mononym

for _, row in artist_df.iterrows():
    last = str(row["Surname for index"]).strip()
    first = str(row["Other names"]).strip()
    
    # Skip invalid entries
    if last and last.lower() not in {"", "nan", "unknown"}:
        has_first = first and first.lower() not in {"", "nan", "unknown"}
        full_name = f"{first} {last}" if has_first else last
        artist_name_map[last.lower()] = full_name

print(f"✅ Loaded {len(artist_name_map)} artist mappings (surname → full name).")

# ---------------------------
# Load concept words
# ---------------------------
print("Loading concept words from CSV...")
df_concepts = pd.read_csv(CONCEPT_CSV)
word_to_categories = defaultdict(list)

for category in df_concepts.columns:
    words = df_concepts[category].dropna().astype(str)
    for word in words:
        w_clean = word.strip().lower()
        if w_clean == "accompölished":
            w_clean = "accomplished"
        if w_clean and len(w_clean) >= 2:
            word_to_categories[w_clean].append(category)

target_words = set(word_to_categories.keys())
print(f"Loaded {len(target_words)} unique concept words.")

# ---------------------------
# Aggregators (use lowercase first name as key)
# ---------------------------
total_counts = defaultdict(int)
artist_counts = defaultdict(lambda: defaultdict(int))      # word → first_name_lower → count
artist_doc_totals = defaultdict(int)                      # first_name_lower → total docs
sentiment_counts = defaultdict(lambda: defaultdict(int))
concept_counts = defaultdict(lambda: defaultdict(int))
year_counts = defaultdict(lambda: defaultdict(int))
category_counts = defaultdict(lambda: defaultdict(int))
artist_snippets = defaultdict(lambda: defaultdict(list))  # word → artist → [snippets]


def trim_sentence(sentence, max_len):
    if len(sentence) <= max_len:
        return sentence
    prefix = sentence[:max_len]
    cut_idx = max(prefix.rfind('.'), prefix.rfind('!'), prefix.rfind('?'))
    if cut_idx != -1:
        return prefix[:cut_idx + 1].rstrip()
    return sentence

# ---------------------------
# Process input CSV
# ---------------------------
print(f"Processing {INPUT_CSV}...")

for chunk in pd.read_csv(INPUT_CSV, chunksize=CHUNK_SIZE):
    chunk['matched_artists'] = chunk['matched_artists'].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else (x or [])
    )
    chunk['concept'] = chunk['concept'].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else (x or [])
    )

    for _, row in chunk.iterrows():
        full_text = str(row.get('Full_text', ''))
        # Extract artist names as strings, strip, and normalize to lowercase for matching
        artists_raw = [a.strip() for a in row['matched_artists'] if isinstance(a, str)]
        artists = [a.lower() for a in artists_raw if a]  # keys for aggregation
        concepts = [c for c in row['concept'] if isinstance(c, str)]
        doc_category = row.get('Category', 'Unknown')
        sentiment = str(row.get('Sentiment', 'neutral')).strip().lower() or 'neutral'

        if pd.isna(doc_category) or doc_category == "":
            doc_category = "Unknown"

        if not artists or not concepts:
            continue

        year = "0000"
        date_val = row.get('Date')
        if pd.notna(date_val) and isinstance(date_val, str):
            yr_match = re.search(r'\b(19|20)\d{2}\b', date_val)
            if yr_match:
                year = yr_match.group(0)

        tokens = set(re.findall(r'\b\w+\b', full_text.lower()))
        matched_words = tokens & target_words

        # Capture longest sentence snippet per word in this doc, then attach to each artist
        if matched_words and full_text:
            sentences = re.split(r'(?<=[.!?])\s+', full_text.strip())
            if not sentences or sentences == [""]:
                sentences = [full_text.strip()]
            best_snippet_by_word = {}
            for sentence in sentences:
                sentence_clean = " ".join(sentence.split())
                if not sentence_clean:
                    continue
                sentence_tokens = set(re.findall(r'\b\w+\b', sentence_clean.lower()))
                word_hits = sentence_tokens & matched_words
                if not word_hits:
                    continue
                snippet = trim_sentence(sentence_clean, MAX_SNIPPET_LEN)
                for word in word_hits:
                    current = best_snippet_by_word.get(word, "")
                    if len(snippet) > len(current):
                        best_snippet_by_word[word] = snippet
            for word, snippet in best_snippet_by_word.items():
                for artist in artists:
                    artist_snippets[word][artist].append(snippet)

        # Update total doc count per artist (by lowercase first name)
        for artist in artists:
            artist_doc_totals[artist] += 1

        for word in matched_words:
            total_counts[word] += 1
            sentiment_counts[word][sentiment] += 1
            for concept in concepts:
                concept_counts[word][concept] += 1
            year_counts[word][year] += 1
            category_counts[word][doc_category] += 1
            for artist in artists:
                artist_counts[word][artist] += 1

# ---------------------------
# Build final results with FULL NAMES
# ---------------------------
results = []
for word in target_words:
    total = total_counts[word]
    if total == 0:
        continue

    # Normalize sentiment, concept, category by total word occurrences
    def to_percent(d, total):
        return {k: round((v / total) * 100, 2) for k, v in d.items()}

    norm_sentiment = to_percent(sentiment_counts[word], total)
    norm_concept = to_percent(concept_counts[word], total)
    norm_category = to_percent(category_counts[word], total)

    # Build artist dictionaries with FULL NAMES
    artist_counts_full = {}
    artist_counts_norm_full = {}
    artist_snippets_full = {}

    for first_key, count in artist_counts[word].items():
        # Map to full name; if not found, use capitalized version of input (e.g., "simon" → "Simon")
        full_name = artist_name_map.get(first_key, first_key.capitalize())

        artist_counts_full[full_name] = count

        total_docs = artist_doc_totals.get(first_key, 1)
        pct = round((count / total_docs) * 100, 2)
        artist_counts_norm_full[full_name] = pct

    for first_key, snippets in artist_snippets[word].items():
        full_name = artist_name_map.get(first_key, first_key.capitalize())
        artist_snippets_full[full_name] = snippets

    doc = {
        "Word": word,
        "WordConcept": word_to_categories[word],
        "TotalCount": total,
        "ArtistSnippets": artist_snippets_full,
        "ArtistCounts": artist_counts_full,              # ✅ raw counts, FULL NAMES
        "ArtistCountsNormalized": artist_counts_norm_full,  # ✅ normalized, FULL NAMES
        "SentimentCounts": norm_sentiment,               # % of word occurrences
        "ConceptCounts": norm_concept,                   # % of word occurrences
        "YearCounts": dict(year_counts[word]),           # raw counts
        "CategoryCounts": norm_category                  # % of word occurrences
    }
    results.append(doc)

# ---------------------------
# Save to MongoDB
# ---------------------------
print(f"Inserting {len(results)} records into MongoDB...")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[RESULT_COLLECTION]

collection.delete_many({})
collection.insert_many(results)

print("✅ Done! All artist fields now use full names (First + Last).")
print("   Sentiment/Concept/Category are normalized by word occurrence.")
print("   ArtistCounts = raw, ArtistCountsNormalized = per-artist document percentage.")
