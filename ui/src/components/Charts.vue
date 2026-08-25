<script setup>
import { useWordStore } from '../stores/WordStore';
import { ref, watch, onMounted, onUnmounted, computed, nextTick } from 'vue';
import Chart from 'chart.js/auto';

const store = useWordStore();

let chart1 = null;
let chart2 = null;
let chart3 = null;
let chart5 = null;
let modalChart = null;

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

// Modal Expand State
const expandedChart = ref(null); // 'timeline' | 'category' | 'sentiment' | 'artist' | null

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

const destroyModalChart = () => {
  if (modalChart) {
    modalChart.destroy();
    modalChart = null;
  }
};

const results = computed(() => store.getResults || []);

const activeConceptRecord = computed(() => {
  if (!results.value.length) return null;
  if (!activeConceptSnippetTab.value) return results.value[0];
  return results.value.find((r) => r.Word === activeConceptSnippetTab.value) || results.value[0];
});

// Chart Data Builders
const getTimelineData = (currentResults) => {
  const all_years = new Set();
  currentResults.forEach((result) => {
    (result.YearCounts || []).forEach((item) => {
      if (item.year && item.year >= 1700 && item.year <= 2030) {
        all_years.add(item.year);
      }
    });
  });

  const line_labels = all_years.size
    ? Array.from(all_years).sort((a, b) => a - b)
    : [1800, 1850, 1900, 1950, 2000];

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
          data: [12, 19, 35, 28, 45],
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          tension: 0.2,
        }
      ];

  return { labels: line_labels, datasets: line_datasets };
};

const getCategoryData = (currentResults) => {
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

  return { labels: category_labels, datasets: category_datasets };
};

const getSentimentData = (currentResults) => {
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

  return { labels: all_sentiments, datasets: sentiment_datasets };
};

const getArtistData = (currentResults, maxArtists = 12) => {
  const top_artists_set = new Set();
  currentResults.forEach((result) => {
    (result.ArtistCounts || []).slice(0, maxArtists).forEach((item) => {
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
        hoverOffset: 10,
      }))
    : [
        {
          label: 'Sample',
          data: [40, 25, 20, 15, 10, 8],
          backgroundColor: ['#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6', '#14b8a6'],
          hoverOffset: 10
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

  return { labels: donut_labels, datasets: donut_datasets, artistMetaMap, artistSnippetMap };
};

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
  const timelineData = getTimelineData(currentResults);
  chart1 = new Chart(ctx1, {
    type: 'line',
    data: timelineData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            title: (items) => `Year: ${items[0]?.label || ''}`,
            label: (item) => ` #${item.dataset.label}: ${item.formattedValue} mentions`
          }
        }
      },
      scales: {
        x: {
          ticks: { autoSkip: true, maxTicksLimit: 14, maxRotation: 0 },
          grid: { display: false }
        },
        y: { beginAtZero: true, ticks: { precision: 0 } }
      }
    }
  });

  // 2. Bar Chart: Categories
  const categoryData = getCategoryData(currentResults);
  chart2 = new Chart(ctx2, {
    type: 'bar',
    data: categoryData,
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
          ticks: { callback: (value) => `${value}%` }
        }
      }
    }
  });

  // 3. Sentiment Chart
  const sentimentData = getSentimentData(currentResults);
  chart5 = new Chart(ctx5, {
    type: 'bar',
    data: sentimentData,
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
          ticks: { callback: (value) => `${value}%` }
        }
      }
    }
  });

  // 4. Donut Chart: Artists
  const { labels: donut_labels, datasets: donut_datasets, artistMetaMap, artistSnippetMap } = getArtistData(currentResults, 12);

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
              return word ? `Word: #${word} - ${value} mentions${pctStr}` : `${value}`;
            },
          },
        },
      },
    },
  });
};

// Render Modal Chart when expanded
const renderModalChart = async () => {
  destroyModalChart();
  await nextTick();

  const modalCanvas = document.getElementById('modal-chart-canvas');
  if (!modalCanvas || !expandedChart.value) return;

  const currentResults = store.getResults || [];

  if (expandedChart.value === 'timeline') {
    const timelineData = getTimelineData(currentResults);
    modalChart = new Chart(modalCanvas, {
      type: 'line',
      data: timelineData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { position: 'top', labels: { font: { size: 13, weight: 'bold' } } },
          tooltip: {
            padding: 12,
            callbacks: {
              title: (items) => `Year: ${items[0]?.label || ''}`,
              label: (item) => ` #${item.dataset.label}: ${item.formattedValue} mentions`
            }
          }
        },
        scales: {
          x: {
            ticks: { autoSkip: true, maxTicksLimit: 25, font: { size: 12 } },
            grid: { color: 'rgba(0, 0, 0, 0.05)' }
          },
          y: {
            beginAtZero: true,
            ticks: { precision: 0, font: { size: 12 } },
            grid: { color: 'rgba(0, 0, 0, 0.05)' }
          }
        }
      }
    });
  } else if (expandedChart.value === 'category') {
    const categoryData = getCategoryData(currentResults);
    modalChart = new Chart(modalCanvas, {
      type: 'bar',
      data: categoryData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { font: { size: 13, weight: 'bold' } } },
          tooltip: {
            padding: 12,
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
          x: { ticks: { font: { size: 12, weight: '500' } } },
          y: {
            beginAtZero: true,
            ticks: { callback: (val) => `${val}%`, font: { size: 12 } }
          }
        }
      }
    });
  } else if (expandedChart.value === 'sentiment') {
    const sentimentData = getSentimentData(currentResults);
    modalChart = new Chart(modalCanvas, {
      type: 'bar',
      data: sentimentData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { font: { size: 13, weight: 'bold' } } },
          tooltip: {
            padding: 12,
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
          x: { ticks: { font: { size: 13, weight: '500' } } },
          y: {
            beginAtZero: true,
            ticks: { callback: (val) => `${val}%`, font: { size: 12 } }
          }
        }
      }
    });
  } else if (expandedChart.value === 'artist') {
    const { labels: donut_labels, datasets: donut_datasets, artistMetaMap, artistSnippetMap } = getArtistData(currentResults, 24);

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

    modalChart = new Chart(modalCanvas, {
      type: 'doughnut',
      data: { labels: donut_labels, datasets: donut_datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        onHover: (_event, elements, chart) => {
          if (!elements?.length) return;
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
          legend: { position: 'right', labels: { font: { size: 12 } } },
          tooltip: {
            padding: 12,
            callbacks: {
              title: (items) => items[0]?.label || '',
              label: (item) => {
                const word = item.dataset.label || '';
                const artist = item.label || '';
                const value = item.formattedValue ?? item.raw ?? '';
                const pct = artistMetaMap[word]?.[artist]?.percentage;
                const pctStr = pct !== undefined ? ` (${pct}%)` : '';
                return word ? `Word: #${word} - ${value} mentions${pctStr}` : `${value}`;
              }
            }
          }
        }
      }
    });
  }
};

const openExpandModal = (chartKey) => {
  expandedChart.value = chartKey;
  renderModalChart();
};

const closeExpandModal = () => {
  expandedChart.value = null;
  destroyModalChart();
};

const handleKeyDown = (e) => {
  if (e.key === 'Escape' && expandedChart.value) {
    closeExpandModal();
  }
};

onMounted(() => {
  renderCharts();
  window.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  destroyAllCharts();
  destroyModalChart();
  window.removeEventListener('keydown', handleKeyDown);
});

watch(
  () => store.getResults,
  () => {
    renderCharts();
    if (expandedChart.value) {
      renderModalChart();
    }
  },
  { deep: true }
);

const modalTitle = computed(() => {
  if (expandedChart.value === 'timeline') return '📈 Expression Timeline (1785–2008)';
  if (expandedChart.value === 'category') return '🎨 Artistic Categories Distribution';
  if (expandedChart.value === 'sentiment') return '💭 Sentiment Breakdown';
  if (expandedChart.value === 'artist') return '🎭 Artist Associations & Percentages';
  return 'Expanded Chart';
});

const modalSubtitle = computed(() => {
  if (expandedChart.value === 'timeline') return 'Historical frequency trajectories across 200+ years of criticism.';
  if (expandedChart.value === 'category') return 'Normalized percentage allocation across the 9 primary cultural categories.';
  if (expandedChart.value === 'sentiment') return 'Comparative sentiment breakdown for all searched concepts.';
  if (expandedChart.value === 'artist') return 'Detailed breakdown of top artists critiqued with this aesthetic descriptor.';
  return '';
});
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
    <!-- Grid of 4 Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 1. Timeline Chart -->
      <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 space-y-4 relative group">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
              <span>📈 Expression Timeline</span>
            </h3>
            <span class="text-xs text-slate-400">Historical mentions by year (1785–2008)</span>
          </div>

          <!-- Maximize Button -->
          <button
            @click="openExpandModal('timeline')"
            class="p-1.5 text-slate-400 hover:text-sky-600 hover:bg-sky-50 rounded-lg border border-transparent hover:border-sky-200 transition-all"
            title="Maximize Timeline Chart"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        </div>

        <div class="h-72">
          <canvas id="line"></canvas>
        </div>
      </div>

      <!-- 2. Category Breakdown Chart -->
      <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 space-y-4 relative group">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
              <span>🎨 Artistic Categories</span>
            </h3>
            <span class="text-xs text-slate-400">Distribution across 9 primary categories</span>
          </div>

          <!-- Maximize Button -->
          <button
            @click="openExpandModal('category')"
            class="p-1.5 text-slate-400 hover:text-sky-600 hover:bg-sky-50 rounded-lg border border-transparent hover:border-sky-200 transition-all"
            title="Maximize Categories Chart"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        </div>

        <div class="h-72">
          <canvas id="bar-category"></canvas>
        </div>
      </div>

      <!-- 3. Sentiment Breakdown Chart -->
      <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 space-y-4 relative group">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
              <span>💭 Sentiment Distribution</span>
            </h3>
            <span class="text-xs text-slate-400">Positive, Neutral, Negative & Mixed</span>
          </div>

          <!-- Maximize Button -->
          <button
            @click="openExpandModal('sentiment')"
            class="p-1.5 text-slate-400 hover:text-sky-600 hover:bg-sky-50 rounded-lg border border-transparent hover:border-sky-200 transition-all"
            title="Maximize Sentiment Chart"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        </div>

        <div class="h-72">
          <canvas id="bar-sentiment"></canvas>
        </div>
      </div>

      <!-- 4. Artist Distribution Donut Chart with Percentages -->
      <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 space-y-4 relative group">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
              <span>🎭 Artist Associations & Percentages</span>
            </h3>
            <span class="text-xs text-slate-400">Top artists critiqued with this concept</span>
          </div>

          <!-- Maximize Button -->
          <button
            @click="openExpandModal('artist')"
            class="p-1.5 text-slate-400 hover:text-sky-600 hover:bg-sky-50 rounded-lg border border-transparent hover:border-sky-200 transition-all"
            title="Maximize Artist Chart"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
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

    <!-- ========================================================================= -->
    <!-- EXPANDED CHART MODAL (LIGHTBOX / SPOTLIGHT VIEW) -->
    <!-- ========================================================================= -->
    <div
      v-if="expandedChart"
      class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/70 backdrop-blur-sm transition-all"
      @click.self="closeExpandModal"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <!-- Modal Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div>
            <h3 class="text-lg font-bold text-slate-900 flex items-center gap-2">
              {{ modalTitle }}
            </h3>
            <p class="text-xs text-slate-500 mt-0.5">
              {{ modalSubtitle }}
            </p>
          </div>

          <div class="flex items-center gap-2">
            <button
              @click="closeExpandModal"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-200/80 hover:bg-slate-300 text-slate-700 text-xs font-bold transition-colors shadow-sm"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              <span>Minimize (Esc)</span>
            </button>
          </div>
        </div>

        <!-- Modal Body -->
        <div class="p-6 flex-1 overflow-y-auto space-y-6">
          <div class="h-[52vh] min-h-[380px] w-full relative">
            <canvas id="modal-chart-canvas"></canvas>
          </div>

          <!-- Extra details if expanded chart is artist -->
          <div v-if="expandedChart === 'artist'" class="rounded-xl border border-slate-200 bg-slate-50/80 p-4 space-y-3">
            <div class="flex items-center justify-between">
              <h4 class="text-xs font-bold text-slate-800 uppercase tracking-wider">
                🎭 Extended Artist Details & Interactive Snippets
              </h4>
              <span class="text-xs text-slate-500">Click any chart slice above to preview contextual snippets</span>
            </div>

            <div v-if="selectedWord" class="p-3 bg-white rounded-xl border border-slate-200 space-y-2">
              <div class="flex items-center justify-between">
                <p class="text-xs font-bold text-slate-800">
                  Snippets for <strong class="text-indigo-700">{{ selectedArtist }}</strong> with #{{ selectedWord }}
                  <span v-if="selectedPercentage" class="text-slate-500 font-normal">({{ selectedPercentage }} of word occurrences)</span>
                </p>
                <button
                  @click="selectedWord = ''"
                  class="text-[10px] text-slate-500 hover:text-slate-800 font-bold"
                >
                  ✕ Clear Selection
                </button>
              </div>
              <div class="max-h-48 overflow-y-auto space-y-2 pr-1">
                <p
                  v-for="(snippet, index) in selectedSnippets"
                  :key="index"
                  class="text-xs bg-slate-50 p-2.5 rounded-lg border border-slate-100 text-slate-700 leading-relaxed"
                  v-html="highlightWord(snippet, selectedWord)"
                ></p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
