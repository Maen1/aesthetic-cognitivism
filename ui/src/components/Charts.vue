<script setup>
import { useWordStore } from '../stores/WordStore';
import { ref, watch, onMounted, onUnmounted, computed } from 'vue';
import Chart from 'chart.js/auto';

const store = useWordStore();

let chart1 = null;
let chart2 = null;
let chart3 = null;
let chart5 = null;

const hoveredArtist = ref('');
const hoveredWord = ref('');
const hoveredCount = ref('');
const hoveredPercentage = ref('');
const selectedArtist = ref('');
const selectedWord = ref('');
const selectedCount = ref('');
const selectedPercentage = ref('');
const selectedSnippets = ref([]);
const activeConceptSnippetTab = ref('');

const escapeHtml = (value) =>
  String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');

const escapeRegExp = (value) =>
  String(value || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const highlightWord = (text, word) => {
  const safe = escapeHtml(text);
  if (!word) return safe;
  const regex = new RegExp(`(${escapeRegExp(word)})`, 'gi');
  return safe.replace(
    regex,
    '<mark class="bg-amber-200 text-amber-900 font-semibold px-1 rounded">$1</mark>'
  );
};

function seededRandom(seed) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function getRandomColor(seed, alpha = 1) {
  const palette = [
    [59, 130, 246],  // Blue
    [236, 72, 153],  // Pink
    [16, 185, 129],  // Emerald
    [245, 158, 11],  // Amber
    [139, 92, 246],  // Purple
    [239, 68, 68],   // Red
    [14, 165, 233],  // Sky
    [20, 184, 166],  // Teal
  ];
  const [r, g, b] = palette[seed % palette.length] || [
    Math.floor(seededRandom(seed + 10) * 200) + 30,
    Math.floor(seededRandom(seed + 11) * 200) + 30,
    Math.floor(seededRandom(seed + 12) * 200) + 30
  ];
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const destroyAllCharts = () => {
  if (chart1) { chart1.destroy(); chart1 = null; }
  if (chart2) { chart2.destroy(); chart2 = null; }
  if (chart3) { chart3.destroy(); chart3 = null; }
  if (chart5) { chart5.destroy(); chart5 = null; }
};

const results = computed(() => store.getResults || []);

const activeConceptRecord = computed(() => {
  if (!results.value.length) return null;
  if (!activeConceptSnippetTab.value) return results.value[0];
  return results.value.find((r) => r.Word === activeConceptSnippetTab.value) || results.value[0];
});

const renderCharts = () => {
  destroyAllCharts();

  const ctx1 = document.getElementById('line');
  const ctx2 = document.getElementById('bar-category');
  const ctx3 = document.getElementById('pie');
  const ctx5 = document.getElementById('bar-sentiment');

  if (!ctx1 || !ctx2 || !ctx3 || !ctx5) return;

  const currentResults = store.getResults || [];

  if (currentResults.length && !activeConceptSnippetTab.value) {
    activeConceptSnippetTab.value = currentResults[0].Word;
  }

  // 1. Line Chart: Years
  const all_years = new Set();
  currentResults.forEach((result) => {
    (result.YearCounts || []).forEach((item) => {
      if (item.year) all_years.add(item.year);
    });
  });

  const line_labels = all_years.size
    ? Array.from(all_years).sort((a, b) => a - b)
    : [1985, 1990, 1995, 2000];

  const line_datasets = currentResults.length
    ? currentResults.map((result, index) => ({
        label: result.Word,
        data: line_labels.map((year) => {
          const entry = (result.YearCounts || []).find((item) => item.year === year);
          return entry ? entry.count : 0;
        }),
        fill: false,
        borderColor: getRandomColor(index),
        backgroundColor: getRandomColor(index, 0.2),
        tension: 0.2,
      }))
    : [
        {
          label: 'Sample: beautiful',
          data: [12, 19, 35, 28],
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          tension: 0.2,
        }
      ];

  chart1 = new Chart(ctx1, {
    type: 'line',
    data: { labels: line_labels, datasets: line_datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
      scales: { y: { beginAtZero: true } }
    }
  });

  // 2. Bar Chart: 9 Primary Canonical Categories
  const category_labels = [
    'Theater & Drama',
    'Concerts & Music',
    'Art & Exhibitions',
    'Films & Cinema',
    'Opera',
    'Dance & Ballet',
    'Poetry & Literature',
    'Television & Radio',
    'Multiple / Other'
  ];

  const category_datasets = currentResults.length
    ? currentResults.map((result, index) => ({
        label: result.Word,
        data: category_labels.map((category) => {
          const entry = (result.CategoryCounts || []).find((item) => item.category === category);
          return entry ? entry.count : 0;
        }),
        borderColor: getRandomColor(index),
        backgroundColor: getRandomColor(index, 0.65),
        borderWidth: 1,
      }))
    : [
        {
          label: 'Sample: beautiful',
          data: [12.79, 37.13, 17.16, 5.87, 9.77, 3.46, 6.45, 1.22, 5.37],
          backgroundColor: 'rgba(59, 130, 246, 0.65)',
          borderColor: 'rgb(59, 130, 246)',
          borderWidth: 1,
        }
      ];

  chart2 = new Chart(ctx2, {
    type: 'bar',
    data: { labels: category_labels, datasets: category_datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: (item) => {
              const word = item.dataset.label || '';
              const value = item.formattedValue ?? item.raw ?? '';
              return word ? `Word: #${word} - ${value}%` : `${value}%`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => `${value}%`
          }
        }
      }
    }
  });

  // 3. Sentiment Chart: Primary Sentiments
  const all_sentiments = ['Positive', 'Neutral', 'Negative', 'Mixed'];
  const sentiment_datasets = currentResults.length
    ? currentResults.map((result, index) => ({
        label: result.Word,
        data: all_sentiments.map((sentiment) => {
          const entry = (result.SentimentCounts || []).find((item) => item.sentiment?.toLowerCase() === sentiment.toLowerCase());
          return entry ? entry.count : 0;
        }),
        borderColor: getRandomColor(index),
        backgroundColor: getRandomColor(index, 0.65),
        borderWidth: 1,
      }))
    : [
        {
          label: 'Sample: beautiful',
          data: [65, 25, 8, 2],
          backgroundColor: ['rgba(16, 185, 129, 0.65)', 'rgba(100, 116, 139, 0.65)', 'rgba(239, 68, 68, 0.65)', 'rgba(245, 158, 11, 0.65)'],
          borderColor: ['rgb(16, 185, 129)', 'rgb(100, 116, 139)', 'rgb(239, 68, 68)', 'rgb(245, 158, 11)'],
          borderWidth: 1
        }
      ];

  chart5 = new Chart(ctx5, {
    type: 'bar',
    data: { labels: all_sentiments, datasets: sentiment_datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: (item) => {
              const word = item.dataset.label || '';
              const value = item.formattedValue ?? item.raw ?? '';
              return word ? `Word: #${word} - ${value}%` : `${value}%`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => `${value}%`
          }
        }
      }
    }
  });


  // 4. Donut Chart: Artists with Percentages
  const top_artists_set = new Set();
  currentResults.forEach((result) => {
    (result.ArtistCounts || []).slice(0, 12).forEach((item) => {
      if (item.artist) top_artists_set.add(item.artist);
    });
  });

  const donut_labels = top_artists_set.size
    ? Array.from(top_artists_set)
    : ['Beethoven', 'Mozart', 'Brahms', 'Bach', 'Shakespeare', 'Pinter'];

  const artistMetaMap = {};
  currentResults.forEach((result) => {
    (result.ArtistCounts || []).forEach((item) => {
      if (!artistMetaMap[result.Word]) artistMetaMap[result.Word] = {};
      artistMetaMap[result.Word][item.artist] = {
        count: item.count,
        percentage: item.percentage || 0
      };
    });
  });

  const donut_datasets = currentResults.length
    ? currentResults.map((result, index) => ({
        label: result.Word,
        data: donut_labels.map((artist) => {
          const entry = (result.ArtistCounts || []).find((item) => item.artist === artist);
          return entry ? entry.count : 0;
        }),
        backgroundColor: donut_labels.map((_, i) => getRandomColor(i, 0.75)),
        hoverOffset: 8,
      }))
    : [
        {
          label: 'Sample',
          data: [40, 25, 20, 15, 10, 8],
          backgroundColor: ['#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6', '#14b8a6'],
          hoverOffset: 8
        }
      ];

  const artistSnippetMap = {};
  currentResults.forEach((result) => {
    const byArtist = {};
    (result.ArtistSnippets || []).forEach((entry) => {
      byArtist[entry.artist] = entry.snippets || [];
    });
    artistSnippetMap[result.Word] = byArtist;
  });

  const getSliceInfo = (chart, element) => {
    if (!element) return null;
    const dataset = chart.data.datasets[element.datasetIndex];
    const word = dataset?.label || '';
    const artist = chart.data.labels?.[element.index] || '';
    const count = dataset?.data?.[element.index] ?? '';
    const pct = artistMetaMap[word]?.[artist]?.percentage ?? '';
    const snippets = artistSnippetMap[word]?.[artist] || [];
    return { artist, word, count, percentage: pct, snippets };
  };

  chart3 = new Chart(ctx3, {
    type: 'doughnut',
    data: { labels: donut_labels, datasets: donut_datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      onHover: (_event, elements, chart) => {
        if (!elements?.length) {
          hoveredArtist.value = '';
          hoveredWord.value = '';
          hoveredCount.value = '';
          hoveredPercentage.value = '';
          return;
        }
        const info = getSliceInfo(chart, elements[0]);
        if (!info) return;
        hoveredArtist.value = info.artist;
        hoveredWord.value = info.word;
        hoveredCount.value = info.count;
        hoveredPercentage.value = info.percentage ? `${info.percentage}%` : '';
      },
      onClick: (_event, elements, chart) => {
        if (!elements?.length) return;
        const info = getSliceInfo(chart, elements[0]);
        if (!info) return;
        selectedArtist.value = info.artist;
        selectedWord.value = info.word;
        selectedCount.value = info.count;
        selectedPercentage.value = info.percentage ? `${info.percentage}%` : '';
        selectedSnippets.value = info.snippets;
      },
      plugins: {
        legend: { position: 'right' },
        tooltip: {
          enabled: true,
          callbacks: {
            title: (items) => items[0]?.label || '',
            label: (item) => {
              const word = item.dataset.label || '';
              const artist = item.label || '';
              const value = item.formattedValue ?? item.raw ?? '';
              const pct = artistMetaMap[word]?.[artist]?.percentage;
              const pctStr = pct !== undefined ? ` (${pct}%)` : '';
              return word ? `Word: ${word} - ${value} mentions${pctStr}` : `${value}`;
            },
          },
        },
      },
    },
  });
};

onMounted(() => {
  renderCharts();
});

onUnmounted(() => {
  destroyAllCharts();
});

watch(
  () => store.getResults,
  () => {
    renderCharts();
  },
  { deep: true }
);
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
    <!-- Grid of Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 1. Timeline Chart -->
      <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 space-y-4">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
            <span>📈 Expression Timeline</span>
          </h3>
          <span class="text-xs text-slate-400">Historical mentions by year</span>
        </div>
        <div class="h-72">
          <canvas id="line"></canvas>
        </div>
      </div>

      <!-- 2. Category Breakdown Chart -->
      <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 space-y-4">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
            <span>🎨 Artistic Categories</span>
          </h3>
          <span class="text-xs text-slate-400">Distribution across genres</span>
        </div>
        <div class="h-72">
          <canvas id="bar-category"></canvas>
        </div>
      </div>

      <!-- 3. Sentiment Breakdown Chart -->
      <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 space-y-4">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
            <span>💭 Sentiment Distribution</span>
          </h3>
          <span class="text-xs text-slate-400">Positive, Neutral & Negative</span>
        </div>
        <div class="h-72">
          <canvas id="bar-sentiment"></canvas>
        </div>
      </div>

      <!-- 4. Artist Distribution Donut Chart with Percentages -->
      <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 space-y-4">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
            <span>🎭 Artist Associations & Percentages</span>
          </h3>
          <span class="text-xs text-slate-400">Top artists critiqued with this concept</span>
        </div>

        <div class="h-72">
          <canvas id="pie"></canvas>
        </div>

        <!-- Interactive Snippet Inspection Box -->
        <div class="mt-4 rounded-xl border border-slate-200 bg-slate-50/70 p-4 space-y-2">
          <div v-if="hoveredWord">
            <p class="text-sm font-semibold text-slate-900">
              {{ hoveredArtist }}
            </p>
            <p class="text-xs text-slate-600">
              Concept: <strong class="text-slate-800">#{{ hoveredWord }}</strong> &middot;
              <strong class="text-indigo-700">{{ hoveredCount }} mentions</strong>
              <span v-if="hoveredPercentage" class="ml-1 text-slate-500">({{ hoveredPercentage }} of word)</span>
            </p>
          </div>
          <p v-else class="text-xs text-slate-500">
            Hover over a chart slice to view artist share, or click a slice to load artist-specific sentence snippets.
          </p>

          <div v-if="selectedWord" class="pt-2 border-t border-slate-200 space-y-2">
            <div class="flex items-center justify-between">
              <p class="text-xs font-bold text-slate-800">
                Snippets for {{ selectedArtist }} &middot; #{{ selectedWord }} ({{ selectedCount }} mentions{{ selectedPercentage ? ', ' + selectedPercentage : '' }})
              </p>
              <button
                @click="selectedWord = ''"
                class="text-[10px] text-slate-500 hover:text-slate-800 font-semibold"
              >
                ✕ Clear
              </button>
            </div>
            <div class="max-h-48 overflow-y-auto space-y-1.5 pr-1">
              <p
                v-for="(snippet, index) in selectedSnippets"
                :key="`${selectedArtist}-${index}`"
                class="text-xs bg-white p-2.5 rounded-lg border border-slate-200/80 text-slate-700 leading-relaxed"
                v-html="highlightWord(snippet, selectedWord)"
              ></p>
              <p v-if="!selectedSnippets.length" class="text-xs text-slate-400 italic">
                No snippets available for this artist/word combination.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 5. Dedicated Concept Context Snippets Section -->
    <div v-if="results.length" class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
            <span>📖 Contextual Concept Snippets</span>
          </h3>
          <p class="text-xs text-slate-500">
            Representative sentences extracted from historical reviews where the searched concept appears.
          </p>
        </div>

        <!-- Concept Switcher Tabs -->
        <div class="flex flex-wrap items-center gap-1.5 self-start sm:self-auto">
          <button
            v-for="res in results"
            :key="res.Word"
            @click="activeConceptSnippetTab = res.Word"
            :class="[
              'text-xs font-semibold px-3 py-1 rounded-lg border transition-colors',
              activeConceptSnippetTab === res.Word
                ? 'bg-amber-500 text-white border-amber-500 shadow-sm'
                : 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200'
            ]"
          >
            #{{ res.Word }} ({{ res.TotalCount }})
          </button>
        </div>
      </div>

      <!-- Snippets Display Grid -->
      <div v-if="activeConceptRecord" class="space-y-2">
        <div class="flex items-center justify-between text-xs text-slate-600">
          <span>Showing context snippets for <strong class="text-slate-900">#{{ activeConceptRecord.Word }}</strong>:</span>
          <span class="text-slate-400">{{ activeConceptRecord.ConceptSnippets?.length || 0 }} samples available</span>
        </div>

        <div v-if="activeConceptRecord.ConceptSnippets?.length" class="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-1">
          <div
            v-for="(snippet, sIdx) in activeConceptRecord.ConceptSnippets"
            :key="sIdx"
            class="bg-amber-50/60 p-3 rounded-xl border border-amber-200/70 text-xs text-slate-800 leading-relaxed space-y-1"
          >
            <div class="text-[10px] text-amber-800 font-bold uppercase tracking-wider">Example {{ sIdx + 1 }}</div>
            <p v-html="highlightWord(snippet, activeConceptRecord.Word)"></p>
          </div>
        </div>

        <p v-else class="text-xs text-slate-400 italic p-4 text-center bg-slate-50 rounded-xl">
          No direct sentence snippets recorded for this concept.
        </p>
      </div>
    </div>
  </div>
</template>
