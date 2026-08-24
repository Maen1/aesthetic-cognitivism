<script setup>
import { onMounted, ref, computed, watch } from 'vue';
import { useCriticismStore } from '../stores/CriticismStore';

const store = useCriticismStore();

// Local filter state
const searchInput = ref('');
const artistInput = ref('');
const authorInput = ref('');
const selectedConceptSnippet = ref(null);
const expandedTextId = ref(null);

let debounceTimer = null;
const handleSearchDebounced = () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    store.searchQuery = searchInput.value;
    store.currentPage = 1;
    store.searchCriticisms();
  }, 350);
};

const handleArtistDebounced = () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    store.selectedArtist = artistInput.value;
    store.currentPage = 1;
    store.searchCriticisms();
  }, 350);
};

const handleAuthorDebounced = () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    store.selectedAuthor = authorInput.value;
    store.currentPage = 1;
    store.searchCriticisms();
  }, 350);
};

const selectCategory = (catValue) => {
  store.setCategory(catValue);
};

const selectSentiment = (sentValue) => {
  store.setSentiment(sentValue);
};

const resetAll = () => {
  searchInput.value = '';
  artistInput.value = '';
  authorInput.value = '';
  selectedConceptSnippet.value = null;
  expandedTextId.value = null;
  store.resetFilters();
};

const toggleFullText = (id) => {
  expandedTextId.value = expandedTextId.value === id ? null : id;
};

const toggleConceptSnippet = (docId, concept, snippetList) => {
  const key = `${docId}_${concept}`;
  if (selectedConceptSnippet.value?.key === key) {
    selectedConceptSnippet.value = null;
  } else {
    selectedConceptSnippet.value = {
      key,
      docId,
      concept,
      snippets: snippetList || []
    };
  }
};

const escapeHtml = (value) =>
  String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');

const escapeRegExp = (value) =>
  String(value || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const highlightKeyword = (text, keyword) => {
  const safe = escapeHtml(text);
  if (!keyword) return safe;
  const regex = new RegExp(`(${escapeRegExp(keyword)})`, 'gi');
  return safe.replace(
    regex,
    '<mark class="bg-amber-200 text-amber-900 font-semibold px-1 rounded">$1</mark>'
  );
};

const getCategoryBadgeClass = (category) => {
  const cat = String(category || '').toLowerCase();
  if (cat.includes('film') || cat.includes('movie') || cat.includes('cinema')) return 'bg-purple-100 text-purple-800 border-purple-200';
  if (cat.includes('theater') || cat.includes('theatre') || cat.includes('drama') || cat.includes('play')) return 'bg-amber-100 text-amber-800 border-amber-200';
  if (cat.includes('concert') || cat.includes('music') || cat.includes('rock') || cat.includes('jazz')) return 'bg-emerald-100 text-emerald-800 border-emerald-200';
  if (cat.includes('art') || cat.includes('exhibit') || cat.includes('museum') || cat.includes('gallery')) return 'bg-blue-100 text-blue-800 border-blue-200';
  if (cat.includes('opera')) return 'bg-rose-100 text-rose-800 border-rose-200';
  if (cat.includes('dance') || cat.includes('ballet')) return 'bg-pink-100 text-pink-800 border-pink-200';
  if (cat.includes('poetry') || cat.includes('literature') || cat.includes('book')) return 'bg-teal-100 text-teal-800 border-teal-200';
  if (cat.includes('tv') || cat.includes('television') || cat.includes('radio')) return 'bg-indigo-100 text-indigo-800 border-indigo-200';
  return 'bg-slate-100 text-slate-800 border-slate-200';
};

const getSentimentBadgeClass = (sentiment) => {
  const sent = String(sentiment || '').toLowerCase();
  if (sent.includes('pos')) return 'bg-green-100 text-green-800 border-green-200';
  if (sent.includes('neg')) return 'bg-rose-100 text-rose-800 border-rose-200';
  if (sent.includes('mix')) return 'bg-amber-100 text-amber-800 border-amber-200';
  return 'bg-slate-100 text-slate-700 border-slate-200';
};

// 8 Primary Canonical Category Groups
const primaryCategories = [
  { label: 'All Categories', value: 'All', icon: '🌐' },
  { label: 'Theater & Drama', value: 'Theater & Drama', icon: '🎭' },
  { label: 'Concerts & Music', value: 'Concerts & Music', icon: '🎵' },
  { label: 'Art & Exhibitions', value: 'Art & Exhibitions', icon: '🖼️' },
  { label: 'Films & Cinema', value: 'Films & Cinema', icon: '🎬' },
  { label: 'Opera', value: 'Opera', icon: '🎼' },
  { label: 'Dance & Ballet', value: 'Dance & Ballet', icon: '🩰' },
  { label: 'Poetry & Literature', value: 'Poetry & Literature', icon: '📜' },
  { label: 'Television & Radio', value: 'Television & Radio', icon: '📺' },
  { label: 'Multiple / Other', value: 'Multiple / Other', icon: '✨' }
];

const primarySentiments = [
  { label: 'All', value: 'All' },
  { label: 'Positive', value: 'Positive' },
  { label: 'Neutral', value: 'Neutral' },
  { label: 'Negative', value: 'Negative' },
  { label: 'Mixed', value: 'Mixed' }
];

onMounted(() => {
  store.fetchFilterMetadata();
  store.searchCriticisms();
});
</script>

<template>
  <section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
    <!-- Filter Card -->
    <div class="bg-white rounded-2xl shadow-sm border border-slate-200/80 p-5 md:p-6 space-y-5">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <h2 class="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>📰 Criticism Catalog & Explorer</span>
          </h2>
          <p class="text-xs sm:text-sm text-slate-500 mt-0.5">
            Filter through 294,000+ historical reviews with LLM summaries, weighted artist mentions, and contextual concepts.
          </p>
        </div>
        <button
          @click="resetAll"
          class="self-start md:self-auto text-xs font-semibold text-slate-600 hover:text-sky-600 bg-slate-100 hover:bg-sky-50 px-3.5 py-1.5 rounded-lg transition-colors border border-slate-200/80"
        >
          Reset All Filters
        </button>
      </div>

      <!-- Search Inputs Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">Search Keywords / Text</label>
          <input
            v-model="searchInput"
            @input="handleSearchDebounced"
            type="text"
            placeholder="Search titles, summaries, texts..."
            class="w-full text-sm rounded-lg border border-slate-300 px-3 py-2 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">Filter by Artist</label>
          <input
            v-model="artistInput"
            @input="handleArtistDebounced"
            type="text"
            placeholder="e.g. Harold Pinter, Christina Ricci"
            class="w-full text-sm rounded-lg border border-slate-300 px-3 py-2 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">Filter by Critic / Author</label>
          <input
            v-model="authorInput"
            @input="handleAuthorDebounced"
            type="text"
            placeholder="e.g. Geoff Brown, Nightingale"
            class="w-full text-sm rounded-lg border border-slate-300 px-3 py-2 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
          />
        </div>
      </div>

      <!-- Category Filter Group -->
      <div class="space-y-2 pt-1 border-t border-slate-100">
        <div class="text-xs font-bold text-slate-600 uppercase tracking-wider">
          Primary Art & Culture Categories:
        </div>
        <div class="flex flex-wrap items-center gap-1.5">
          <button
            v-for="cat in primaryCategories"
            :key="cat.value"
            @click="selectCategory(cat.value)"
            :class="[
              'inline-flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg transition-all border',
              store.selectedCategory === cat.value
                ? 'bg-sky-600 text-white border-sky-600 shadow-sm font-semibold'
                : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
            ]"
          >
            <span>{{ cat.icon }}</span>
            <span>{{ cat.label }}</span>
          </button>
        </div>
      </div>

      <!-- Sentiment Filter Group -->
      <div class="space-y-2 pt-1 border-t border-slate-100">
        <div class="text-xs font-bold text-slate-600 uppercase tracking-wider">
          Sentiment Analysis:
        </div>
        <div class="flex flex-wrap items-center gap-1.5">
          <button
            v-for="sent in primarySentiments"
            :key="sent.value"
            @click="selectSentiment(sent.value)"
            :class="[
              'text-xs font-medium px-3 py-1.5 rounded-lg transition-all border',
              store.selectedSentiment === sent.value
                ? 'bg-slate-900 text-white border-slate-900 shadow-sm font-semibold'
                : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
            ]"
          >
            {{ sent.label }}
          </button>
        </div>
      </div>

      <!-- Results Stats Bar -->
      <div class="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
        <span v-if="!store.isLoading">
          Showing <strong class="text-slate-800">{{ store.searchResults.length }}</strong> of
          <strong class="text-slate-800">{{ store.totalCount.toLocaleString() }}</strong> criticism articles
        </span>
        <span v-else class="text-sky-600 font-medium animate-pulse">Filtering criticisms...</span>

        <span v-if="store.totalPages > 1">
          Page {{ store.currentPage }} of {{ store.totalPages.toLocaleString() }}
        </span>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="store.errorMessage" class="bg-red-50 border border-red-200 text-red-800 rounded-xl p-4 text-sm">
      {{ store.errorMessage }}
    </div>

    <!-- Loading Skeleton -->
    <div v-if="store.isLoading" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div v-for="n in 4" :key="n" class="bg-white rounded-2xl border border-slate-200 p-6 space-y-4 animate-pulse">
        <div class="h-4 bg-slate-200 rounded w-1/3"></div>
        <div class="h-6 bg-slate-200 rounded w-3/4"></div>
        <div class="h-16 bg-slate-100 rounded"></div>
        <div class="h-4 bg-slate-200 rounded w-1/2"></div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="!store.searchResults.length"
      class="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4"
    >
      <div class="text-4xl">🔍</div>
      <h3 class="text-lg font-bold text-slate-800">No criticisms found</h3>
      <p class="text-sm text-slate-500 max-w-md mx-auto">
        No articles matched your active search criteria or filters. Try adjusting your search query or resetting category/sentiment filters.
      </p>
      <button
        @click="resetAll"
        class="inline-block bg-sky-600 text-white text-xs font-semibold px-4 py-2 rounded-lg hover:bg-sky-500 shadow-sm transition-colors"
      >
        Clear All Filters
      </button>
    </div>

    <!-- Criticism Cards Grid -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <article
        v-for="item in store.searchResults"
        :key="item.id"
        class="bg-white rounded-2xl border border-slate-200/90 shadow-sm hover:shadow-md transition-shadow p-5 md:p-6 flex flex-col justify-between space-y-4"
      >
        <!-- Header -->
        <div class="space-y-2">
          <div class="flex flex-wrap items-center gap-2">
            <span
              :class="['text-xs font-semibold px-2.5 py-0.5 rounded-full border', getCategoryBadgeClass(item.category)]"
            >
              {{ item.category || 'Uncategorized' }}
            </span>
            <span
              :class="['text-xs font-medium px-2 py-0.5 rounded-full border', getSentimentBadgeClass(item.sentiment)]"
            >
              {{ item.sentiment || 'Neutral' }}
            </span>
            <span v-if="item.date || item.year" class="text-xs text-slate-500 ml-auto">
              🗓️ {{ item.date || item.year }}
            </span>
          </div>

          <h3 class="text-base sm:text-lg font-bold text-slate-900 leading-snug">
            {{ item.title || 'Untitled Critique' }}
          </h3>

          <div class="text-xs text-slate-500 flex flex-wrap gap-x-3 gap-y-1">
            <span v-if="item.author" class="font-medium text-slate-700">✍️ {{ item.author }}</span>
            <span v-if="item.publication">📰 {{ item.publication }}</span>
            <span v-if="item.place">📍 {{ item.place }}</span>
          </div>
        </div>

        <!-- LLM Summary Box -->
        <div v-if="item.summary" class="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/60 text-xs sm:text-sm text-slate-700 leading-relaxed">
          <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
            <span>✨ Summary</span>
          </div>
          <p>{{ item.summary }}</p>
        </div>

        <!-- Artists Breakdown -->
        <div v-if="item.artistPercentages && item.artistPercentages.length" class="space-y-1.5">
          <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            🎭 Artists Focus
          </div>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="art in item.artistPercentages"
              :key="art.artist"
              class="inline-flex items-center gap-1 text-xs bg-indigo-50 text-indigo-800 border border-indigo-200/70 px-2 py-0.5 rounded-md font-medium"
            >
              <span>{{ art.artist }}</span>
              <span class="bg-indigo-200/80 text-indigo-900 text-[10px] px-1 rounded font-bold">
                {{ art.percentage }}%
              </span>
            </span>
          </div>
        </div>

        <!-- Concepts & Snippets -->
        <div v-if="item.foundConcepts && item.foundConcepts.length" class="space-y-1.5">
          <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center justify-between">
            <span>💡 Aesthetic & Cognitive Concepts (Click to preview snippet)</span>
          </div>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="concept in item.foundConcepts"
              :key="concept"
              @click="toggleConceptSnippet(item.id, concept, item.conceptSnippets?.find(s => s.concept === concept)?.snippets)"
              :class="[
                'text-xs font-semibold px-2 py-0.5 rounded-md border transition-all',
                selectedConceptSnippet?.key === `${item.id}_${concept}`
                  ? 'bg-amber-400 text-amber-950 border-amber-500 shadow-sm'
                  : 'bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100'
              ]"
            >
              #{{ concept }}
            </button>
          </div>

          <!-- Snippet Drawer for clicked concept -->
          <div
            v-if="selectedConceptSnippet?.docId === item.id"
            class="mt-2 p-3 bg-amber-50/70 rounded-xl border border-amber-200 text-xs text-slate-800 space-y-1.5 transition-all"
          >
            <div class="font-semibold text-amber-900 flex items-center justify-between">
              <span>Snippets mentioning "{{ selectedConceptSnippet.concept }}":</span>
              <button
                @click="selectedConceptSnippet = null"
                class="text-[10px] text-amber-700 hover:text-amber-950 font-bold"
              >
                ✕ Close
              </button>
            </div>
            <div v-if="selectedConceptSnippet.snippets?.length" class="space-y-1">
              <p
                v-for="(snip, sIdx) in selectedConceptSnippet.snippets"
                :key="sIdx"
                class="leading-relaxed bg-white/80 p-2 rounded border border-amber-100"
                v-html="highlightKeyword(snip, selectedConceptSnippet.concept)"
              ></p>
            </div>
            <p v-else class="text-slate-500 italic">No exact snippet recorded for this concept in this article.</p>
          </div>
        </div>

        <!-- Full Text Collapsible -->
        <div v-if="expandedTextId === item.id" class="mt-3 pt-3 border-t border-slate-200 space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-700">Full Text Transcript:</span>
            <button
              @click="toggleFullText(item.id)"
              class="text-xs font-medium text-slate-500 hover:text-slate-800"
            >
              Hide Full Text ▲
            </button>
          </div>
          <div class="max-h-72 overflow-y-auto bg-slate-900 text-slate-100 p-4 rounded-xl text-xs font-mono whitespace-pre-wrap leading-relaxed">
            {{ item.fullText || item.extractedText || 'No text content available.' }}
          </div>
        </div>

        <!-- Card Footer Actions -->
        <div class="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
          <button
            @click="toggleFullText(item.id)"
            class="font-semibold text-sky-600 hover:text-sky-700 transition-colors"
          >
            {{ expandedTextId === item.id ? '▲ Collapse Text' : '▼ Read Full Text' }}
          </button>

          <a
            v-if="item.url"
            :href="item.url"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-1 font-semibold text-slate-600 hover:text-sky-600 transition-colors"
          >
            <span>Gale Archive ↗</span>
          </a>
        </div>
      </article>
    </div>

    <!-- Pagination Controls -->
    <div
      v-if="store.totalPages > 1"
      class="bg-white rounded-xl border border-slate-200 p-4 flex flex-col sm:flex-row items-center justify-between gap-4"
    >
      <div class="text-xs text-slate-500">
        Page <strong class="text-slate-800">{{ store.currentPage }}</strong> of
        <strong class="text-slate-800">{{ store.totalPages.toLocaleString() }}</strong>
      </div>

      <div class="flex items-center gap-2">
        <button
          @click="store.setPage(store.currentPage - 1)"
          :disabled="store.isFirstPage"
          class="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          ◀ Previous
        </button>

        <span class="text-xs font-bold text-slate-800 px-2">
          {{ store.currentPage }} / {{ store.totalPages.toLocaleString() }}
        </span>

        <button
          @click="store.setPage(store.currentPage + 1)"
          :disabled="store.isLastPage"
          class="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Next ▶
        </button>
      </div>
    </div>
  </section>
</template>
