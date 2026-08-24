from pymongo import MongoClient
from collections import defaultdict

client = MongoClient("mongodb://localhost:27017")
db = client["aesthetic"]
collection = db["criticism"]
result_collection = db["word_counts"]

def count_words_by_author_and_year(word_list):
    results = []
    data = list(collection.find({"Full_text": {"$ne": None}, "Category": {"$ne": None}, "Date": {"$ne": None}}))
    
    # Initialize a dictionary to hold counts
    word_counts = defaultdict(lambda: {
        'TotalCount': 0,
        'WordConcept':[],
        'CategoryCounts': defaultdict(int),
        'AuthorCounts': defaultdict(int),
        'YearCounts': defaultdict(int)
    })

    for doc in data:
        full_text = doc.get('Full_text', '')
        author = doc.get('Author')
        year = 0000
        
        # Extract year from Date if possible
        if doc.get('Date'):
            year = doc['Date'][:4]  # Simple year extraction
        
        for i in range(len(word_list)):
            word = word_list[i]["word"]
            count = full_text.lower().count(word.lower())  # Case insensitive count
            if count > 0:
                word_counts[word]["WordConcept"] = word_list[i]["category"]
                word_counts[word]['TotalCount'] += count
                word_counts[word]['CategoryCounts'][doc['Category']] += count
                word_counts[word]['AuthorCounts'][author] += count
                if year:
                    word_counts[word]['YearCounts'][year] += count

    # Prepare results to insert into the result collection
    for word, counts in word_counts.items():
        results.append({
            'Word': word,
            "WordConcept": counts["WordConcept"],
            'TotalCount': counts['TotalCount'],
            'CategoryCounts': dict(counts['CategoryCounts']),
            'AuthorCounts': dict(counts['AuthorCounts']),
            'YearCounts': dict(counts['YearCounts'])
        })

    # Insert results into the new collection
    result_collection.insert_many(results)

    return results

# Example usage
word_list = [
    {"word": "revolutionary", "category": ["Aesthetic", "Historical", "Cognitive"]},
    {"word": "overwhelming", "category": ["Emotion"]},
    {"word": "philosophical", "category": ["Cognitive"]},
    {"word": "infinite", "category": ["Cognitive"]},
    {"word": "pathetic", "category": ["Emotion"]},
    {"word": "elusive", "category": ["Cognitive"]},
    {"word": "gracious", "category": ["Aesthetic"]},
    {"word": "sad", "category": ["Emotion"]},
    {"word": "picturesque", "category": ["Descriptive"]},
    {"word": "limpid", "category": ["Descriptive"]},
    {"word": "melancholy", "category": ["Emotion"]},
    {"word": "authentic", "category": ["Evaluative"]},
    {"word": "polished", "category": ["Evaluative"]},
    {"word": "persuasive", "category": ["Cognitive"]},
    {"word": "poetical", "category": ["Descriptive"]},
    {"word": "complex", "category": ["Cognitive"]},
    {"word": "sublime", "category": ["Aesthetic"]},
    {"word": "extreme", "category": ["Descriptive"]},
    {"word": "balanced", "category": ["Aesthetic"]},
    {"word": "dark", "category": ["Descriptive"]},
    {"word": "passionate", "category": ["Emotion"]},
    {"word": "eloquent", "category": ["Descriptive"]},
    {"word": "clean", "category": ["Descriptive"]},
    {"word": "profound", "category": ["Cognitive"]},
    {"word": "elegant", "category": ["Aesthetic"]},
    {"word": "melodious", "category": ["Descriptive"]},
    {"word": "strange", "category": ["Descriptive"]},
    {"word": "enjoyable", "category": ["Emotion"]},
    {"word": "agreeable", "category": ["Emotion"]},
    {"word": "efficient", "category": ["Descriptive"]},
    {"word": "imaginative", "category": ["Cognitive"]},
    {"word": "human", "category": ["Descriptive"]},
    {"word": "noble", "category": ["Descriptive"]},
    {"word": "graceful", "category": ["Aesthetic"]},
    {"word": "poetic", "category": ["Descriptive"]},
    {"word": "exquisite", "category": ["Aesthetic"]},
    {"word": "individual", "category": ["Descriptive"]},
    {"word": "powerful", "category": ["Aesthetic"]},
    {"word": "delighted", "category": ["Emotion"]},
    {"word": "delicate", "category": ["Aesthetic"]},
    {"word": "extraordinary", "category": ["Descriptive"]},
    {"word": "genuine", "category": ["Evaluative"]},
    {"word": "splendid", "category": ["Descriptive"]},
    {"word": "fair", "category": ["Descriptive"]},
    {"word": "clever", "category": ["Cognitive"]},
    {"word": "lyrical", "category": ["Descriptive"]},
    {"word": "emotional", "category": ["Emotion"]},
    {"word": "wonderful", "category": ["Emotion"]},
    {"word": "charming", "category": ["Descriptive"]},
    {"word": "expressive", "category": ["Aesthetic"]},
    {"word": "light", "category": ["Descriptive"]},
    {"word": "happy", "category": ["Emotion"]},
    {"word": "artistic", "category": ["Descriptive"]},
    {"word": "difficult", "category": ["Descriptive"]},
    {"word": "dramatic", "category": ["Descriptive"]},
    {"word": "original", "category": ["Historical"]},
    {"word": "remarkable", "category": ["Descriptive"]},
    {"word": "brilliant", "category": ["Descriptive"]},
    {"word": "romantic", "category": ["Historical"]},
    {"word": "clear", "category": ["Descriptive"]},
    {"word": "successful", "category": ["Cognitive"]},
    {"word": "beautiful", "category": ["Aesthetic"]},
]
def main():
    results = count_words_by_author_and_year(word_list)
    for result in results:
        print(result['Word'])
        print(result['TotalCount'])
        print(result['WordConcept'])

if __name__ == "__main__":
    main()
