import { defineStore } from "pinia";

export const useWordStore = defineStore('Word', {
  state: () => ({ 
	count: 0, 
	name: 'Eduardo',
	searchTerm: '',
	words:[],
	results:[]	

	}),

  getters: {
	doubleCount: (state) => state.count * 2,
	getWords: (state) => state.words,
	getWordsLength: (state) => state.words.length,
	getResults: (state) => state.results
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

	setResults(results){
		this.results = results
	},

	async searchExpressions() {
		if (!this.searchTerm.trim()) return; // Avoid sending empty searches
		
		const words =  JSON.stringify(this.searchTerm.split(/\s+/).filter(word => word.trim()));
		this.searchWords(JSON.parse(words))
		console.log("words to query",JSON.parse(words))


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
			const GRAPHQL_ENDPOINT = 'http://130.238.146.150/api/graphql/'; // replace with your actual endpoint
			const response = await fetch(GRAPHQL_ENDPOINT, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({ query }),
			});
			const result = await response.json();
			this.setResults(result.data["wordCounts"])

			console.log("results: ", result.data["wordCounts"]); // Handle the response data
		} catch (error) {
			console.error('Error fetching data:', error);
		}
	}
  },
})