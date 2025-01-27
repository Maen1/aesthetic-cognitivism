<script setup>
import { ref } from 'vue';

// GraphQL endpoint
const GRAPHQL_ENDPOINT = 'http://localhost:8000/graphql/'; // replace with your actual endpoint

// Search state
const searchTerm = ref('');

// Define the function to send the search to GraphQL API
const searchExpressions = async () => {
  if (!searchTerm.value.trim()) return; // Avoid sending empty searches
  
  const words =  JSON.stringify(searchTerm.value.split(/\s+/).filter(word => word.trim()));
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
};
</script>

<template>
  <main class="px-4 md:px-0 pt-8">
    <div class="max-w-8xl mx-auto bg-slate-50 py-8 rounded-lg px-4 md:px-0">
      <div class="mx-auto max-w-2xl text-center">
        <h2 class="text-lg font-bold tracking-tight text-gray-900 sm:text-xl">Search for Expressions</h2>
      </div>
      <form @submit.prevent="searchExpressions" class="mx-auto mt-8 max-w-xl bg-slate-50">
        <div class="grid grid-cols-1 gap-x-8 gap-y-6 sm:grid-cols-2">
          <div class="sm:col-span-2">
            <label for="search" class="block text-sm font-semibold leading-6 text-gray-900">Search for:</label>
            <input
              type="text"
              id="search"
              v-model="searchTerm"
              autocomplete="given-name"
              class="block w-full rounded-md border-0 px-3.5 py-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-sky-600 sm:text-sm sm:leading-6"
              placeholder="start typing :)"
            />
          </div>
        </div>
        <div class="mt-8">
          <button
            type="submit"
            class="block w-full rounded-md bg-sky-600 px-4 py-3 text-center text-sm font-semibold text-white shadow-sm hover:bg-sky-500"
          >
            Search
          </button>
        </div>
      </form>
    </div>
  </main>
</template>
