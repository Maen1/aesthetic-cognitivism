import { defineStore } from 'pinia';

const getGraphQLEndpoint = () => {
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost' && window.location.port === '5173') {
    return 'http://localhost:8000/api/graphql/';
  }
  return '/api/graphql/';
};

export const useWordStore = defineStore('Word', {
  state: () => ({
    count: 0,
    name: 'Eduardo',
    searchTerm: '',
    words: [],
    results: [],
    metricMode: 'normalized', // 'normalized' | 'raw'
    isLoading: false,
    errorMessage: null
  }),

  getters: {
    doubleCount: (state) => state.count * 2,
    getWords: (state) => state.words,
    getWordsLength: (state) => state.words.length,
    getResults: (state) => state.results,
    getMetricMode: (state) => state.metricMode,
  },

  actions: {
    increment() {
      this.count++;
    },

    setMetricMode(mode) {
      this.metricMode = mode === 'raw' ? 'raw' : 'normalized';
    },

    searchWords(words) {
      this.words = words;
    },

    setSearchTerm(searchTerm) {
      this.searchTerm = searchTerm;
    },

    setResults(results) {
      this.results = results || [];
    },

    async searchExpressions() {
      if (!this.searchTerm || !this.searchTerm.trim()) return;

      const parsedWords = this.searchTerm
        .split(/\s+/)
        .map((w) => w.trim().toLowerCase())
        .filter(Boolean);

      if (!parsedWords.length) return;

      this.searchWords(parsedWords);
      this.isLoading = true;
      this.errorMessage = null;

      const query = `
        query GetWordCounts($words: [String!]!) {
          wordCounts(words: $words) {
            Word
            TotalCount
            WordConcept
            ArtistSnippets {
              artist
              snippets
            }
            CategoryCounts {
              category
              count
              rawCount
              normalizedCount
              totalRecords
            }
            ArtistCounts {
              artist
              count
              percentage
            }
            ConceptCounts {
              concept
              count
            }
            ConceptSnippets {
              snippet
              publication
              date
              year
              title
              author
              era
            }

            SentimentCounts {
              sentiment
              count
              rawCount
              normalizedCount
              totalRecords
            }
            YearCounts {
              year
              count
              normalizedCount
              totalRecords
            }
          }
        }
      `;

      try {
        const response = await fetch(getGraphQLEndpoint(), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query,
            variables: { words: parsedWords }
          }),
        });

        const result = await response.json();
        if (result.errors && result.errors.length) {
          throw new Error(result.errors[0].message);
        }
        this.setResults(result.data?.wordCounts || []);
      } catch (error) {
        console.error('Error fetching word counts:', error);
        this.errorMessage = error.message || 'Failed to fetch word statistics.';
        this.setResults([]);
      } finally {
        this.isLoading = false;
      }
    },
  },
});
