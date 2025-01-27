import { defineStore } from "pinia";

export const useWordStore = defineStore('Word', {
  state: () => ({ 
	count: 0, 
	name: 'Eduardo',
	searchTerm: '',
	words:[]
	}),

  getters: {
	doubleCount: (state) => state.count * 2,
	getWords: (state) => state.words
  },
  actions: {
	increment() {
	  this.count++
	},

	searchWords(words){
		this.words = words
		console.log(this.words)
	},

	setSearchTerm(searchTerm){
		this.searchTerm = searchTerm
	},

	async searchExpressions() {
		if (!this.searchTerm.trim()) return; // Avoid sending empty searches
		
		const words =  JSON.stringify(this.searchTerm.split(/\s+/).filter(word => word.trim()));
		this.searchWords(words)
		console.log(words)

		const query = `
				{ 
				wordCounts(words: ${words}) {
					Word
					TotalCount
					CategoryCounts {
					category 
					count
					}
					AuthorCounts {
					author 
					count
					}
					YearCounts {
					year 
					count
					}
				}
			}
		`;


		try {
			const GRAPHQL_ENDPOINT = 'http://localhost:8000/graphql/'; // replace with your actual endpoint
			const response = await fetch(GRAPHQL_ENDPOINT, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({ query }),
			});
			const result = await response.json();

			console.log(result.data); // Handle the response data
		} catch (error) {
			console.error('Error fetching data:', error);
		}
	}
  },
})