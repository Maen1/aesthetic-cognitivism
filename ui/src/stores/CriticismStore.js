import { defineStore } from 'pinia';

const getGraphQLEndpoint = () => {
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost' && window.location.port === '5173') {
    return 'http://localhost:8000/api/graphql/';
  }
  return '/api/graphql/';
};

export const useCriticismStore = defineStore('Criticism', {
  state: () => ({
    searchQuery: '',
    selectedCategory: 'All',
    selectedSentiment: 'All',
    selectedArtist: '',
    selectedAuthor: '',
    selectedConcept: '',
    currentPage: 1,
    pageSize: 12,
    searchResults: [],
    totalCount: 0,
    totalPages: 1,
    filterMetadata: {
      categories: [],
      sentiments: [],
      totalCriticisms: 0
    },
    isLoading: false,
    errorMessage: null,
    activeCriticism: null
  }),

  getters: {
    hasResults: (state) => state.searchResults.length > 0,
    isFirstPage: (state) => state.currentPage <= 1,
    isLastPage: (state) => state.currentPage >= state.totalPages
  },

  actions: {
    async fetchFilterMetadata() {
      const query = `
        query {
          filterMetadata {
            categories
            sentiments
            totalCriticisms
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
        if (result.data?.filterMetadata) {
          this.filterMetadata = result.data.filterMetadata;
        }
      } catch (err) {
        console.error('Failed to fetch filter metadata:', err);
      }
    },

    async searchCriticisms() {
      this.isLoading = true;
      this.errorMessage = null;

      const query = `
        query Search(
          $query: String
          $artist: String
          $author: String
          $category: String
          $sentiment: String
          $concept: String
          $page: Int
          $pageSize: Int
        ) {
          searchCriticisms(
            query: $query
            artist: $artist
            author: $author
            category: $category
            sentiment: $sentiment
            concept: $concept
            page: $page
            pageSize: $pageSize
          ) {
            items {
              id
              author
              title
              publication
              date
              dateEpoch
              year
              place
              fullText
              extractedText
              url
              category
              sentiment
              source
              summary
              artistPercentages {
                artist
                percentage
              }
              foundConcepts
              conceptSnippets {
                concept
                snippets
              }
            }
            total
            page
            pageSize
            totalPages
          }
        }
      `;

      const variables = {
        query: this.searchQuery.trim() || null,
        artist: this.selectedArtist.trim() || null,
        author: this.selectedAuthor.trim() || null,
        category: this.selectedCategory !== 'All' ? this.selectedCategory : null,
        sentiment: this.selectedSentiment !== 'All' ? this.selectedSentiment : null,
        concept: this.selectedConcept.trim() || null,
        page: this.currentPage,
        pageSize: this.pageSize
      };

      try {
        const response = await fetch(getGraphQLEndpoint(), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, variables })
        });
        const result = await response.json();
        if (result.errors && result.errors.length) {
          throw new Error(result.errors[0].message);
        }
        const data = result.data?.searchCriticisms;
        if (data) {
          this.searchResults = data.items || [];
          this.totalCount = data.total || 0;
          this.currentPage = data.page || 1;
          this.totalPages = data.totalPages || 1;
        }
      } catch (err) {
        console.error('Error searching criticisms:', err);
        this.errorMessage = err.message || 'Failed to load criticisms.';
        this.searchResults = [];
        this.totalCount = 0;
        this.totalPages = 1;
      } finally {
        this.isLoading = false;
      }
    },

    setPage(page) {
      if (page < 1 || (this.totalPages && page > this.totalPages)) return;
      this.currentPage = page;
      this.searchCriticisms();
    },

    setSearchQuery(q) {
      this.searchQuery = q;
      this.currentPage = 1;
      this.searchCriticisms();
    },

    setCategory(category) {
      this.selectedCategory = category;
      this.currentPage = 1;
      this.searchCriticisms();
    },

    setSentiment(sentiment) {
      this.selectedSentiment = sentiment;
      this.currentPage = 1;
      this.searchCriticisms();
    },

    setArtist(artist) {
      this.selectedArtist = artist;
      this.currentPage = 1;
      this.searchCriticisms();
    },

    setAuthor(author) {
      this.selectedAuthor = author;
      this.currentPage = 1;
      this.searchCriticisms();
    },

    setConcept(concept) {
      this.selectedConcept = concept;
      this.currentPage = 1;
      this.searchCriticisms();
    },

    resetFilters() {
      this.searchQuery = '';
      this.selectedCategory = 'All';
      this.selectedSentiment = 'All';
      this.selectedArtist = '';
      this.selectedAuthor = '';
      this.selectedConcept = '';
      this.currentPage = 1;
      this.searchCriticisms();
    },

    openCriticism(item) {
      this.activeCriticism = item;
    },

    closeCriticism() {
      this.activeCriticism = null;
    }
  }
});
