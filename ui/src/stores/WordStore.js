import { defineStore } from 'pinia';

const getGraphQLEndpoint = () => {
  if (
    typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') &&
    window.location.port !== '8000'
  ) {
    return `http://${window.location.hostname}:8000/api/graphql/`;
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
    missingWords: [],
    hasSearched: false,
    availableConcepts: [],
    isLoadingAvailableConcepts: false,
    selectedCategory: 'All',
    selectedArtist: '',
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
    getSelectedCategory: (state) => state.selectedCategory,
    getSelectedArtist: (state) => state.selectedArtist,
    hasActiveFilters: (state) =>
      (state.selectedCategory && state.selectedCategory !== 'All') ||
      Boolean(state.selectedArtist && state.selectedArtist.trim()),
  },

  actions: {
    increment() {
      this.count++;
    },

    setMetricMode(mode) {
      this.metricMode = mode === 'raw' ? 'raw' : 'normalized';
    },

    setCategory(category) {
      this.selectedCategory = category || 'All';
      if (this.hasSearched && this.words.length) {
        this.searchExpressions();
      }
    },

    setArtist(artist) {
      this.selectedArtist = artist || '';
      if (this.hasSearched && this.words.length) {
        this.searchExpressions();
      }
    },

    resetFilters() {
      this.selectedCategory = 'All';
      this.selectedArtist = '';
      if (this.hasSearched && this.words.length) {
        this.searchExpressions();
      }
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
      this.missingWords = [];
      this.hasSearched = true;

      const query = `
        query GetWordCounts($words: [String!]!, $category: String, $artist: String) {
          wordCounts(words: $words, category: $category, artist: $artist) {
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
            variables: {
              words: parsedWords,
              category: this.selectedCategory !== 'All' ? this.selectedCategory : null,
              artist: this.selectedArtist.trim() || null
            }
          }),
        });

        const result = await response.json();
        if (result.errors && result.errors.length) {
          throw new Error(result.errors[0].message);
        }
        const foundResults = result.data?.wordCounts || [];
        const foundWords = foundResults.map((r) => (r.Word || '').toLowerCase());
        const missing = parsedWords.filter((w) => !foundWords.includes(w));

        this.missingWords = missing;
        this.setResults(foundResults);

        if (foundResults.length === 0 || foundResults.every((r) => r.TotalCount === 0)) {
          const filterDetails = [];
          if (this.selectedCategory && this.selectedCategory !== 'All') {
            filterDetails.push(`Artform: ${this.selectedCategory}`);
          }
          if (this.selectedArtist && this.selectedArtist.trim()) {
            filterDetails.push(`Artist: ${this.selectedArtist.trim()}`);
          }
          if (filterDetails.length) {
            this.errorMessage = `No records found for concept(s) ${parsedWords.map((w) => `"${w}"`).join(', ')} matching active filter (${filterDetails.join(', ')}).`;
          } else if (parsedWords.length === 1) {
            this.errorMessage = `Concept "${parsedWords[0]}" was not found in the 273 curated aesthetic vocabulary concepts.`;
          } else {
            this.errorMessage = `None of the searched concepts (${parsedWords.map((w) => `"${w}"`).join(', ')}) were found in the 273 curated aesthetic vocabulary concepts.`;
          }
        }
      } catch (error) {
        console.error('Error fetching word counts:', error);
        this.errorMessage = error.message || 'Failed to fetch word statistics.';
        this.setResults([]);
      } finally {
        this.isLoading = false;
      }
    },

    clearError() {
      this.errorMessage = null;
    },

    resetSearch() {
      this.searchTerm = '';
      this.words = [];
      this.results = [];
      this.missingWords = [];
      this.selectedCategory = 'All';
      this.selectedArtist = '';
      this.hasSearched = false;
      this.errorMessage = null;
    },

    async fetchAvailableConcepts() {
      if (this.availableConcepts.length) return;
      this.isLoadingAvailableConcepts = true;
      const query = `
        query GetAvailableConcepts {
          availableConcepts {
            word
            totalCount
          }
        }
      `;
      try {
        const response = await fetch(getGraphQLEndpoint(), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query })
        });
        const result = await response.json();
        this.availableConcepts = result.data?.availableConcepts || [];
      } catch (err) {
        console.error('Failed to load available concepts:', err);
      } finally {
        this.isLoadingAvailableConcepts = false;
      }
    },

    toggleSelectedConcept(conceptWord) {
      const word = conceptWord.trim().toLowerCase();
      const current = this.searchTerm
        .split(/\s+/)
        .map((w) => w.trim().toLowerCase())
        .filter(Boolean);

      const idx = current.indexOf(word);
      if (idx >= 0) {
        current.splice(idx, 1);
      } else {
        current.push(word);
      }
      this.searchTerm = current.join(' ');
      this.words = current;
    },

    removeSelectedConcept(conceptWord) {
      const word = conceptWord.trim().toLowerCase();
      const current = this.searchTerm
        .split(/\s+/)
        .map((w) => w.trim().toLowerCase())
        .filter(Boolean);

      const updated = current.filter((w) => w !== word);
      this.searchTerm = updated.join(' ');
      this.words = updated;
    },

    clearSelectedConcepts() {
      this.searchTerm = '';
      this.words = [];
    },
  },
});
