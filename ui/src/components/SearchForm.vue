<script setup>
import { useWordStore } from '../stores/WordStore';
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';

const store = useWordStore();

const searchTerm = ref('');
const exampleWords = ['beautiful', 'dramatic', 'original', 'melancholic', 'brilliant', 'poignant', 'authentic', 'sublime'];

// Multi-Select Dropdown State
const isDropdownOpen = ref(false);
const dropdownRef = ref(null);
const conceptSearchQuery = ref('');
const sortBy = ref('frequency'); // 'frequency' | 'alpha'

// Sync searchTerm when store.searchTerm changes externally
watch(
  () => store.searchTerm,
  (newVal) => {
    if (newVal !== searchTerm.value) {
      searchTerm.value = newVal || '';
    }
  }
);

// Parsed active words
const selectedWords = computed(() => {
  return searchTerm.value
    .split(/\s+/)
    .map((w) => w.trim().toLowerCase())
    .filter(Boolean);
});

const isWordSelected = (word) => {
  return selectedWords.value.includes(word.toLowerCase());
};

const toggleWord = (word) => {
  const w = word.trim().toLowerCase();
  const current = [...selectedWords.value];
  const idx = current.indexOf(w);
  if (idx >= 0) {
    current.splice(idx, 1);
  } else {
    current.push(w);
  }
  searchTerm.value = current.join(' ');
  store.setSearchTerm(searchTerm.value);
};

const removeWord = (word) => {
  const w = word.trim().toLowerCase();
  const updated = selectedWords.value.filter((item) => item !== w);
  searchTerm.value = updated.join(' ');
  store.setSearchTerm(searchTerm.value);
};

const clearAllSelected = () => {
  searchTerm.value = '';
  store.clearSelectedConcepts();
};

const filteredConcepts = computed(() => {
  const list = store.availableConcepts || [];
  const q = conceptSearchQuery.value.trim().toLowerCase();
  let result = list;
  if (q) {
    result = list.filter((item) => item.word.toLowerCase().includes(q));
  }
  return [...result].sort((a, b) => {
    if (sortBy.value === 'frequency') {
      return (b.totalCount || 0) - (a.totalCount || 0);
    }
    return a.word.localeCompare(b.word);
  });
});

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value;
  if (isDropdownOpen.value) {
    conceptSearchQuery.value = '';
  }
};

const searchExpressions = async () => {
  if (!searchTerm.value.trim()) return;
  isDropdownOpen.value = false;
  store.setSearchTerm(searchTerm.value);
  store.searchExpressions();
};

const applyAndSearch = () => {
  isDropdownOpen.value = false;
  searchExpressions();
};

const pickExample = (word) => {
  toggleWord(word);
  searchExpressions();
};

// 8 Primary Canonical Category Groups + All
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

const popularArtists = ['Shakespeare', 'Beethoven', 'Mozart', 'Bach', 'Picasso', 'Wagner', 'Brahms', 'Pinter'];

const artistInput = ref(store.selectedArtist || '');

watch(
  () => store.selectedArtist,
  (newVal) => {
    if (newVal !== artistInput.value) {
      artistInput.value = newVal || '';
    }
  }
);

let artistDebounceTimer = null;
const handleArtistInputDebounced = () => {
  clearTimeout(artistDebounceTimer);
  artistDebounceTimer = setTimeout(() => {
    store.setArtist(artistInput.value);
  }, 400);
};

const clearArtist = () => {
  artistInput.value = '';
  store.setArtist('');
};

const selectPopularArtist = (artistName) => {
  if (artistInput.value.toLowerCase() === artistName.toLowerCase()) {
    clearArtist();
  } else {
    artistInput.value = artistName;
    store.setArtist(artistName);
  }
};

const selectCategory = (cat) => {
  store.setCategory(cat);
};

const resetAllFilters = () => {
  artistInput.value = '';
  store.resetFilters();
};

const handleGlobalClick = (event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    isDropdownOpen.value = false;
  }
};

const handleKeyDown = (event) => {
  if (event.key === 'Escape' && isDropdownOpen.value) {
    isDropdownOpen.value = false;
  }
};

onMounted(() => {
  store.fetchAvailableConcepts();
  window.addEventListener('click', handleGlobalClick);
  window.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  window.removeEventListener('click', handleGlobalClick);
  window.removeEventListener('keydown', handleKeyDown);
});
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

      <form @submit.prevent="searchExpressions" class="max-w-3xl mx-auto space-y-4">
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <label for="search" class="text-xs font-semibold text-slate-700">
              Search &amp; Select Concept Words:
            </label>
            <span class="text-[11px] text-slate-400">
              {{ selectedWords.length ? `${selectedWords.length} selected` : `${store.availableConcepts.length || 273} curated concepts` }}
            </span>
          </div>

          <div class="flex flex-col sm:flex-row gap-2 relative" ref="dropdownRef">
            <!-- Text Input -->
            <div class="relative flex-1">
              <input
                type="text"
                id="search"
                v-model="searchTerm"
                @focus="isDropdownOpen = false"
                class="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                placeholder="Type or select concepts from dropdown (e.g. sublime dramatic)"
              />
              <button
                v-if="searchTerm"
                type="button"
                @click="clearAllSelected"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-sm font-bold"
                title="Clear input"
              >
                &times;
              </button>
            </div>

            <!-- Multi-Select Dropdown Toggle Button -->
            <button
              type="button"
              @click.stop="toggleDropdown"
              class="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-300 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-100 hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 transition-all select-none"
              :class="isDropdownOpen ? 'border-sky-500 ring-2 ring-sky-500/20 bg-sky-50/50' : ''"
            >
              <span>📚 Concepts</span>
              <span
                v-if="selectedWords.length"
                class="bg-sky-600 text-white text-[11px] font-bold px-1.5 py-0.5 rounded-full"
              >
                {{ selectedWords.length }}
              </span>
              <span
                class="text-xs transition-transform duration-150"
                :class="isDropdownOpen ? 'rotate-180 text-sky-600' : 'text-slate-400'"
              >
                ▼
              </span>
            </button>

            <!-- Primary Analyze CTA -->
            <button
              type="submit"
              :disabled="store.isLoading || !selectedWords.length"
              class="inline-flex items-center justify-center rounded-xl bg-sky-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-sky-500 disabled:opacity-50 transition-colors shrink-0"
            >
              <span v-if="store.isLoading" class="animate-pulse">Searching...</span>
              <span v-else>Analyze Expressions</span>
            </button>

            <!-- ======================================================== -->
            <!-- MULTI-SELECT DROPDOWN MENU POPOVER -->
            <!-- ======================================================== -->
            <div
              v-if="isDropdownOpen"
              class="absolute top-full left-0 right-0 sm:right-auto sm:w-[480px] z-50 mt-2 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-100"
            >
              <!-- Dropdown Header: Filter + Sort Controls -->
              <div class="p-3 bg-slate-50/90 border-b border-slate-100 space-y-2.5">
                <div class="relative">
                  <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs">🔍</span>
                  <input
                    type="text"
                    v-model="conceptSearchQuery"
                    class="w-full pl-8 pr-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500"
                    placeholder="Filter 273 concepts (e.g. sublime, modern, tragic)..."
                    @click.stop
                  />
                  <button
                    v-if="conceptSearchQuery"
                    type="button"
                    @click.stop="conceptSearchQuery = ''"
                    class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs font-bold"
                  >
                    &times;
                  </button>
                </div>

                <div class="flex items-center justify-between text-[11px] text-slate-500 gap-2">
                  <div class="flex items-center gap-1">
                    <span class="font-medium text-slate-400">Sort:</span>
                    <button
                      type="button"
                      @click.stop="sortBy = 'frequency'"
                      class="px-2 py-0.5 rounded-md font-semibold transition-colors"
                      :class="sortBy === 'frequency' ? 'bg-sky-600 text-white' : 'bg-slate-200/80 text-slate-600 hover:bg-slate-300'"
                    >
                      📈 Mentions
                    </button>
                    <button
                      type="button"
                      @click.stop="sortBy = 'alpha'"
                      class="px-2 py-0.5 rounded-md font-semibold transition-colors"
                      :class="sortBy === 'alpha' ? 'bg-sky-600 text-white' : 'bg-slate-200/80 text-slate-600 hover:bg-slate-300'"
                    >
                      🔤 A–Z
                    </button>
                  </div>

                  <div class="flex items-center gap-2">
                    <span class="font-semibold text-slate-700">
                      {{ selectedWords.length }} of {{ store.availableConcepts.length || 273 }} selected
                    </span>
                    <button
                      v-if="selectedWords.length"
                      type="button"
                      @click.stop="clearAllSelected"
                      class="text-red-500 hover:text-red-700 font-medium underline"
                    >
                      Clear
                    </button>
                  </div>
                </div>
              </div>

              <!-- Scrollable Concept Word List -->
              <div class="max-h-72 overflow-y-auto divide-y divide-slate-100 overscroll-contain">
                <div
                  v-for="concept in filteredConcepts"
                  :key="concept.word"
                  @click.stop="toggleWord(concept.word)"
                  class="flex items-center justify-between px-3.5 py-2 hover:bg-sky-50/50 cursor-pointer select-none transition-colors"
                  :class="isWordSelected(concept.word) ? 'bg-sky-50/70 font-semibold' : ''"
                >
                  <div class="flex items-center gap-2.5 min-w-0">
                    <input
                      type="checkbox"
                      :checked="isWordSelected(concept.word)"
                      @click.stop="toggleWord(concept.word)"
                      class="w-4 h-4 rounded text-sky-600 border-slate-300 focus:ring-sky-500 cursor-pointer"
                    />
                    <span
                      class="truncate text-xs"
                      :class="isWordSelected(concept.word) ? 'text-sky-950 font-bold' : 'text-slate-700'"
                    >
                      {{ concept.word }}
                    </span>
                  </div>

                  <span
                    class="text-[10px] px-2 py-0.5 rounded-full shrink-0 font-mono transition-colors"
                    :class="isWordSelected(concept.word) ? 'bg-sky-200 text-sky-900 font-semibold' : 'bg-slate-100 text-slate-500'"
                  >
                    {{ (concept.totalCount || 0).toLocaleString() }}
                  </span>
                </div>

                <!-- Empty Filter Results -->
                <div v-if="filteredConcepts.length === 0" class="p-8 text-center text-xs text-slate-400">
                  No aesthetic concepts match "{{ conceptSearchQuery }}"
                </div>
              </div>

              <!-- Dropdown Footer -->
              <div class="p-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between gap-3">
                <button
                  type="button"
                  @click="isDropdownOpen = false"
                  class="text-xs text-slate-500 hover:text-slate-800 font-medium px-3 py-1.5"
                >
                  Close
                </button>

                <button
                  type="button"
                  @click="applyAndSearch"
                  :disabled="!selectedWords.length"
                  class="text-xs font-semibold px-4 py-1.5 rounded-xl bg-sky-600 text-white hover:bg-sky-500 disabled:opacity-40 transition-colors shadow-sm"
                >
                  Analyze {{ selectedWords.length ? `(${selectedWords.length})` : '' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Selected Tags Pills Display -->
        <div v-if="selectedWords.length" class="flex flex-wrap items-center gap-1.5 pt-1">
          <span class="text-xs text-slate-400 mr-1">Active concepts:</span>
          <span
            v-for="word in selectedWords"
            :key="word"
            class="inline-flex items-center gap-1.5 text-xs bg-sky-50 text-sky-800 border border-sky-200 px-2.5 py-0.5 rounded-lg font-semibold shadow-xs"
          >
            <span>#{{ word }}</span>
            <button
              type="button"
              @click="removeWord(word)"
              class="text-sky-400 hover:text-sky-800 text-sm font-bold leading-none ml-0.5"
              title="Remove concept"
            >
              &times;
            </button>
          </span>
          <button
            type="button"
            @click="clearAllSelected"
            class="text-[11px] text-slate-400 hover:text-slate-600 underline ml-1"
          >
            Clear all
          </button>
        </div>

        <!-- ======================================================== -->
        <!-- ANALYTICS SCOPE FILTERS (ARTFORM & ARTIST) -->
        <!-- ======================================================== -->
        <div class="bg-slate-50/90 rounded-2xl border border-slate-200/90 p-3.5 sm:p-4 space-y-3 shadow-xs">
          <div class="flex items-center justify-between text-xs">
            <div class="flex items-center gap-1.5">
              <span class="font-bold text-slate-800">🔍 Filter Analytics Scope</span>
              <span class="text-[11px] text-slate-400 font-normal hidden sm:inline">(Optional domain &amp; creator filters)</span>
            </div>
            <button
              v-if="store.hasActiveFilters"
              type="button"
              @click="resetAllFilters"
              class="text-xs text-rose-600 hover:text-rose-800 font-semibold flex items-center gap-1 transition-colors bg-rose-50 hover:bg-rose-100 px-2.5 py-1 rounded-lg border border-rose-200/80"
            >
              <span>✕ Clear Filters</span>
            </button>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <!-- Artform Filter -->
            <div>
              <label class="block text-[11px] font-semibold text-slate-600 mb-1">
                🎨 Filter by Artform:
              </label>
              <div class="relative">
                <select
                  :value="store.selectedCategory"
                  @change="selectCategory($event.target.value)"
                  class="w-full text-xs rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-800 shadow-xs focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 font-medium cursor-pointer"
                >
                  <option
                    v-for="cat in primaryCategories"
                    :key="cat.value"
                    :value="cat.value"
                  >
                    {{ cat.icon }} {{ cat.label }}
                  </option>
                </select>
              </div>
            </div>

            <!-- Artist Filter -->
            <div>
              <label class="block text-[11px] font-semibold text-slate-600 mb-1">
                👤 Filter by Artist:
              </label>
              <div class="relative">
                <input
                  type="text"
                  v-model="artistInput"
                  @input="handleArtistInputDebounced"
                  placeholder="e.g. Shakespeare, Beethoven, Mozart..."
                  class="w-full text-xs rounded-xl border border-slate-300 bg-white pl-3 pr-8 py-2 text-slate-800 placeholder:text-slate-400 shadow-xs focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 font-medium"
                />
                <button
                  v-if="artistInput"
                  type="button"
                  @click="clearArtist"
                  class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs font-bold px-1"
                  title="Clear artist filter"
                >
                  &times;
                </button>
              </div>
            </div>
          </div>

          <!-- Popular Artist Quick Chips -->
          <div class="flex flex-wrap items-center gap-1.5 pt-0.5">
            <span class="text-[11px] text-slate-400 mr-0.5">Popular Creators:</span>
            <button
              v-for="art in popularArtists"
              :key="art"
              type="button"
              @click="selectPopularArtist(art)"
              class="text-[11px] px-2 py-0.5 rounded-lg transition-all font-medium border"
              :class="store.selectedArtist.toLowerCase() === art.toLowerCase()
                ? 'bg-sky-600 text-white border-sky-600 shadow-xs font-semibold'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100 hover:text-slate-800'"
            >
              {{ art }}
            </button>
          </div>

          <!-- Active Filter Pill Badges Indicator -->
          <div v-if="store.hasActiveFilters" class="flex flex-wrap items-center gap-1.5 pt-1.5 border-t border-slate-200/60">
            <span class="text-[11px] font-semibold text-sky-900">Active Scope:</span>
            <span
              v-if="store.selectedCategory && store.selectedCategory !== 'All'"
              class="inline-flex items-center gap-1 text-[11px] bg-sky-100 text-sky-800 font-semibold px-2 py-0.5 rounded-md border border-sky-200 shadow-xs"
            >
              <span>🎨 {{ store.selectedCategory }}</span>
              <button type="button" @click="store.setCategory('All')" class="hover:text-sky-950 font-bold ml-0.5">&times;</button>
            </span>
            <span
              v-if="store.selectedArtist && store.selectedArtist.trim()"
              class="inline-flex items-center gap-1 text-[11px] bg-sky-100 text-sky-800 font-semibold px-2 py-0.5 rounded-md border border-sky-200 shadow-xs"
            >
              <span>👤 {{ store.selectedArtist }}</span>
              <button type="button" @click="clearArtist" class="hover:text-sky-950 font-bold ml-0.5">&times;</button>
            </span>
            <span class="text-[10px] text-slate-500 italic ml-1">
              (Showing filtered analytical slice)
            </span>
          </div>
        </div>

        <!-- Not Found / Error Banner -->
        <div
          v-if="store.errorMessage"
          class="rounded-xl border border-amber-200 bg-amber-50/90 p-4 text-xs sm:text-sm text-amber-900 shadow-sm flex items-start gap-3 transition-all"
        >
          <span class="text-lg shrink-0 mt-0.5">⚠️</span>
          <div class="space-y-1 flex-1">
            <div class="flex items-center justify-between">
              <span class="font-bold text-amber-950">Concept Not Found</span>
              <button
                type="button"
                @click="store.clearError"
                class="text-amber-500 hover:text-amber-800 text-base leading-none font-bold px-1"
                title="Dismiss"
              >
                &times;
              </button>
            </div>
            <p class="text-amber-800 leading-relaxed">
              {{ store.errorMessage }}
            </p>
            <p class="text-amber-700/80 text-[11px]">
              The criticism corpus tracks <strong>273 curated aesthetic concepts</strong>. You can browse and select them directly using the <strong>📚 Concepts</strong> dropdown button above.
            </p>
          </div>
        </div>

        <!-- Partial Match Warning -->
        <div
          v-else-if="store.missingWords.length && store.getResults.length"
          class="rounded-xl border border-sky-200 bg-sky-50/80 p-3 text-xs text-sky-900 flex items-center justify-between gap-3 shadow-sm"
        >
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-sm">ℹ️</span>
            <span>
              Showing results for <strong class="text-sky-950">{{ store.getResults.map(r => `#${r.Word}`).join(', ') }}</strong>.
              Not found in 273 concepts:
              <span v-for="w in store.missingWords" :key="w" class="inline-block bg-sky-100 text-sky-800 font-mono px-1.5 py-0.5 rounded text-[11px] font-semibold ml-1">
                "{{ w }}"
              </span>
            </span>
          </div>
          <button
            type="button"
            @click="store.missingWords = []"
            class="text-sky-500 hover:text-sky-800 font-bold px-1"
            title="Dismiss"
          >
            &times;
          </button>
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
            :class="isWordSelected(word) ? 'bg-sky-100 text-sky-800 border-sky-300 font-semibold' : ''"
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
