<script setup>
import { useWordStore } from '../stores/WordStore';
import { ref } from 'vue';

const store = useWordStore();

const exampleWords = ['beautiful', 'dramatic', 'original', 'melancholic', 'brilliant', 'poignant', 'authentic', 'sublime'];

const searchExpressions = async () => {
  if (!searchTerm.value.trim()) return;
  store.setSearchTerm(searchTerm.value);
  store.searchExpressions();
};

const pickExample = (word) => {
  searchTerm.value = word;
  searchExpressions();
};
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
    <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 md:p-8 space-y-6">
      <div class="max-w-3xl text-center mx-auto space-y-2">
        <h2 class="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
          Aesthetic Concept & Expression Analytics
        </h2>
        <p class="text-xs sm:text-sm text-slate-500">
          Compare the historical trajectory, artistic categories, sentiment distribution, and artist associations of critical terms.
        </p>
      </div>

      <form @submit.prevent="searchExpressions" class="max-w-2xl mx-auto space-y-4">
        <div>
          <label for="search" class="block text-xs font-semibold text-slate-700 mb-1.5">
            Search Concept Words (space-separated):
          </label>
          <div class="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              id="search"
              v-model="searchTerm"
              class="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
              placeholder="e.g. beautiful profound emotional"
            />
            <button
              type="submit"
              :disabled="store.isLoading"
              class="inline-flex items-center justify-center rounded-xl bg-sky-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-sky-500 disabled:opacity-50 transition-colors"
            >
              <span v-if="store.isLoading" class="animate-pulse">Searching...</span>
              <span v-else>Analyze Expressions</span>
            </button>
          </div>
        </div>

        <!-- Quick Examples -->
        <div class="flex flex-wrap items-center gap-1.5 pt-1">
          <span class="text-xs text-slate-400 mr-1">Quick Suggestions:</span>
          <button
            v-for="word in exampleWords"
            :key="word"
            type="button"
            @click="pickExample(word)"
            class="text-xs bg-slate-100 text-slate-700 hover:bg-sky-50 hover:text-sky-700 border border-slate-200 px-2.5 py-1 rounded-lg transition-colors font-medium"
          >
            {{ word }}
          </button>
        </div>

        <!-- Results badges -->
        <div v-if="store.getResults.length" class="pt-2 border-t border-slate-100 flex flex-wrap gap-2">
          <span
            v-for="res in store.getResults"
            :key="res.Word"
            class="inline-flex items-center gap-1.5 text-xs bg-sky-50 text-sky-800 border border-sky-200 px-3 py-1 rounded-full font-semibold"
          >
            <span>#{{ res.Word }}</span>
            <span class="bg-sky-200 text-sky-900 text-[10px] px-1.5 py-0.5 rounded-full">{{ res.TotalCount }} occurrences</span>
          </span>
        </div>
      </form>
    </div>
  </div>
</template>
