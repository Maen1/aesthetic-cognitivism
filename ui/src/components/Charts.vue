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
const snippetSortOrder = ref('asc'); // 'asc' = oldest first (1785 → 2008), 'desc' = newest first
const activeSnippetEra = ref('all'); // 'all' | '1785–1849' | '1850–1899' | '1900–1949' | '1950–1979' | '1980–2008'

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

const getSnippetText = (s) => (typeof s === 'object' && s !== null ? s.snippet || '' : String(s || ''));
const getSnippetPub = (s) => (typeof s === 'object' && s !== null ? s.publication : null);
const getSnippetDate = (s) => (typeof s === 'object' && s !== null ? (s.date || (s.year ? String(s.year) : null)) : null);
const getSnippetYear = (s) => (typeof s === 'object' && s !== null ? (s.year ? Number(s.year) : null) : null);
const getSnippetTitle = (s) => (typeof s === 'object' && s !== null ? s.title : null);
const getSnippetAuthor = (s) => (typeof s === 'object' && s !== null ? s.author : null);
const getSnippetEra = (s) => {
  if (typeof s === 'object' && s !== null && s.era) return s.era;
  const yr = getSnippetYear(s);
  if (!yr) return 'Unknown';
  if (yr < 1850) return '1785–1849';
  if (yr < 1900) return '1850–1899';
  if (yr < 1950) return '1900–1949';
  if (yr < 1980) return '1950–1979';
  return '1980–2008';
};

const getEraBadgeInfo = (era) => {
  switch (era) {
    case '1785–1849':
      return { label: 'Romanticism / 18th–19th C.', icon: '🏛️', bg: 'bg-rose-100/90 text-rose-800 border-rose-200' };
    case '1850–1899':
      return { label: 'Victorian / Late 19th C.', icon: '🎩', bg: 'bg-amber-100/90 text-amber-800 border-amber-200' };
    case '1900–1949':
      return { label: 'Modernism / Interwar', icon: '📻', bg: 'bg-emerald-100/90 text-emerald-800 border-emerald-200' };
    case '1950–1979':
      return { label: 'Post-war / Mid-Century', icon: '📺', bg: 'bg-sky-100/90 text-sky-800 border-sky-200' };
    case '1980–2008':
      return { label: 'Contemporary / Turn of Century', icon: '💻', bg: 'bg-purple-100/90 text-purple-800 border-purple-200' };
    default:
      return { label: era || 'Historical', icon: '📜', bg: 'bg-slate-100 text-slate-700 border-slate-200' };
  }
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

const HISTORICAL_ERA_DEFINITIONS = [
  { id: '1785–1849', label: '1785–1849', name: 'Romanticism / Early', icon: '🏛️' },
  { id: '1850–1899', label: '1850–1899', name: 'Victorian', icon: '🎩' },
  { id: '1900–1949', label: '1900–1949', name: 'Modernism', icon: '📻' },
  { id: '1950–1979', label: '1950–1979', name: 'Post-war', icon: '📺' },
  { id: '1980–2008', label: '1980–2008', name: 'Contemporary', icon: '💻' },
];

const availableSnippetEras = computed(() => {
  const list = activeConceptRecord.value?.ConceptSnippets || [];
  const counts = { all: list.length };
  HISTORICAL_ERA_DEFINITIONS.forEach((def) => { counts[def.id] = 0; });
  list.forEach((s) => {
    const era = getSnippetEra(s);
    if (era) {
      counts[era] = (counts[era] || 0) + 1;
    }
  });
  return [
    { id: 'all', label: 'All Eras', name: 'Full Range', icon: '🌐', count: list.length },
    ...HISTORICAL_ERA_DEFINITIONS.map((def) => ({
      ...def,
      count: counts[def.id] || 0
    }))
  ];
});

const processedConceptSnippets = computed(() => {
  const list = activeConceptRecord.value?.ConceptSnippets || [];
  let filtered = [...list];
  if (activeSnippetEra.value !== 'all') {
    filtered = filtered.filter((s) => getSnippetEra(s) === activeSnippetEra.value);
  }
  filtered.sort((a, b) => {
    const ya = getSnippetYear(a) ?? (snippetSortOrder.value === 'asc' ? 9999 : -9999);
    const yb = getSnippetYear(b) ?? (snippetSortOrder.value === 'asc' ? 9999 : -9999);
    if (ya !== yb) {
      return snippetSortOrder.value === 'asc' ? ya - yb : yb - ya;
    }
    const da = getSnippetDate(a) || '';
    const db = getSnippetDate(b) || '';
    return snippetSortOrder.value === 'asc' ? da.localeCompare(db) : db.localeCompare(da);
  });
  return filtered;
});

const toggleSnippetSort = () => {
  snippetSortOrder.value = snippetSortOrder.value === 'asc' ? 'desc' : 'asc';
};

const isNormalized = computed(() => store.getMetricMode === 'normalized');

// Chart Data Builders
const getTimelineData = (currentResults) => {
  const isNorm = store.getMetricMode === 'normalized';
  const all_years = new Set();
  const yearMetaMap = {};

  currentResults.forEach((result) => {
    yearMetaMap[result.Word] = {};
    (result.YearCounts || []).forEach((item) => {
      if (item.year && item.year >= 1700 && item.year <= 2030) {
        all_years.add(item.year);
        yearMetaMap[result.Word][item.year] = {
          raw: item.count || 0,
          normalized: item.normalizedCount ?? 0,
          totalRecords: item.totalRecords ?? null
        };
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
          const meta = yearMetaMap[result.Word]?.[year];
          if (!meta) return 0;
          return isNorm ? meta.normalized : meta.raw;
        }),
        fill: false,
        borderColor: getRandomColor(index),
        backgroundColor: getRandomColor(index, 0.2),
        tension: 0.2,
      }))
    : [
        {
          label: 'Sample: beautiful',
          data: isNorm ? [1.2, 1.8, 3.2, 2.5, 4.1] : [12, 19, 35, 28, 45],
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          tension: 0.2,
        }
      ];

  return { labels: line_labels, datasets: line_datasets, yearMetaMap };
};

const getCategoryData = (currentResults) => {
  const isNorm = store.getMetricMode === 'normalized';
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
  const catMetaMap = {};

  currentResults.forEach((result) => {
    catMetaMap[result.Word] = {};
    (result.CategoryCounts || []).forEach((item) => {
      catMetaMap[result.Word][item.category] = {
        pctShare: item.count || 0,
        raw: item.rawCount ?? 0,
        normalized: item.normalizedCount ?? 0,
        totalRecords: item.totalRecords ?? null
      };
    });
  });

  const category_datasets = currentResults.length
    ? currentResults.map((result, index) => ({
        label: result.Word,
        data: category_labels.map((category) => {
          const meta = catMetaMap[result.Word]?.[category];
          if (!meta) return 0;
          return isNorm ? meta.normalized : meta.pctShare;
        }),
        borderColor: getRandomColor(index),
        backgroundColor: getRandomColor(index, 0.65),
        borderWidth: 1,
      }))
    : [
        {
          label: 'Sample: beautiful',
          data: isNorm
            ? [1.1, 4.5, 1.5, 0.8, 2.8, 1.5, 1.8, 1.5, 1.7]
            : [12.79, 37.13, 17.16, 5.87, 9.77, 3.46, 6.45, 1.22, 5.37],
          backgroundColor: 'rgba(59, 130, 246, 0.65)',
          borderColor: 'rgb(59, 130, 246)',
          borderWidth: 1,
        }
      ];

  return { labels: category_labels, datasets: category_datasets, catMetaMap };
};

const getSentimentData = (currentResults) => {
  const isNorm = store.getMetricMode === 'normalized';
  const all_sentiments = ['Positive', 'Neutral', 'Negative', 'Mixed'];
  const sentMetaMap = {};

  currentResults.forEach((result) => {
    sentMetaMap[result.Word] = {};
    (result.SentimentCounts || []).forEach((item) => {
      sentMetaMap[result.Word][item.sentiment] = {
        pctShare: item.count || 0,
        raw: item.rawCount ?? 0,
        normalized: item.normalizedCount ?? 0,
        totalRecords: item.totalRecords ?? null
      };
    });
  });

  const sentiment_datasets = currentResults.length
    ? currentResults.map((result, index) => ({
        label: result.Word,
        data: all_sentiments.map((sentiment) => {
          const meta = sentMetaMap[result.Word]?.[sentiment];
          if (!meta) return 0;
          return isNorm ? meta.normalized : meta.pctShare;
        }),
        borderColor: getRandomColor(index),
        backgroundColor: getRandomColor(index, 0.65),
        borderWidth: 1,
      }))
    : [
        {
          label: 'Sample: beautiful',
          data: isNorm ? [2.7, 1.7, 1.3, 0.5] : [65, 25, 8, 2],
          backgroundColor: ['rgba(16, 185, 129, 0.65)', 'rgba(100, 116, 139, 0.65)', 'rgba(239, 68, 68, 0.65)', 'rgba(245, 158, 11, 0.65)'],
          borderColor: ['rgb(16, 185, 129)', 'rgb(100, 116, 139)', 'rgb(239, 68, 68)', 'rgb(245, 158, 11)'],
          borderWidth: 1
        }
      ];

  return { labels: all_sentiments, datasets: sentiment_datasets, sentMetaMap };
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
  const isNorm = store.getMetricMode === 'normalized';

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
            label: (item) => {
              const word = item.dataset.label || '';
              const yr = item.label;
              const meta = timelineData.yearMetaMap?.[word]?.[yr];
              if (isNorm && meta) {
                const normVal = meta.normalized.toFixed(3).replace(/\.?0+$/, '');
                const recStr = meta.totalRecords ? ` (${meta.raw} mentions / ${meta.totalRecords.toLocaleString()} records)` : ` (${meta.raw} mentions)`;
                return ` #${word}: ${normVal} per 100 records${recStr}`;
              }
              return ` #${word}: ${item.formattedValue} mentions`;
            }
          }
        }
      },
      scales: {
        x: {
          ticks: { autoSkip: true, maxTicksLimit: 14, maxRotation: 0 },
          grid: { display: false }
        },
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => isNorm ? `${value} / 100 rec` : value
          }
        }
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
      onClick: (_event, elements, chart) => {
        if (!elements?.length) return;
        const index = elements[0].index;
        const clickedCat = chart.data.labels?.[index];
        if (clickedCat) {
          if (store.selectedCategory === clickedCat) {
            store.setCategory('All');
          } else {
            store.setCategory(clickedCat);
          }
        }
      },
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: (item) => {
              const word = item.dataset.label || '';
              const cat = item.label;
              const meta = categoryData.catMetaMap?.[word]?.[cat];
              if (isNorm && meta) {
                const normVal = meta.normalized.toFixed(3).replace(/\.?0+$/, '');
                const recStr = meta.totalRecords ? ` (${meta.raw.toLocaleString()} mentions / ${meta.totalRecords.toLocaleString()} records)` : ` (${meta.raw.toLocaleString()} mentions)`;
                return ` #${word}: ${normVal} per 100 records${recStr}`;
              }
              const value = item.formattedValue ?? item.raw ?? '';
              return word ? `Word: #${word} - ${value}%` : `${value}%`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: (value) => isNorm ? `${value} / 100 rec` : `${value}%` }
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
              const sent = item.label;
              const meta = sentimentData.sentMetaMap?.[word]?.[sent];
              if (isNorm && meta) {
                const normVal = meta.normalized.toFixed(3).replace(/\.?0+$/, '');
                const recStr = meta.totalRecords ? ` (${meta.raw.toLocaleString()} mentions / ${meta.totalRecords.toLocaleString()} records)` : ` (${meta.raw.toLocaleString()} mentions)`;
                return ` #${word}: ${normVal} per 100 records${recStr}`;
              }
              const value = item.formattedValue ?? item.raw ?? '';
              return word ? `Word: #${word} - ${value}%` : `${value}%`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: (value) => isNorm ? `${value} / 100 rec` : `${value}%` }
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
  if (!modalCanvas || !expandedChart.value || expandedChart.value === 'snippets') return;

  const currentResults = store.getResults || [];
  const isNorm = store.getMetricMode === 'normalized';

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
              label: (item) => {
                const word = item.dataset.label || '';
                const yr = item.label;
                const meta = timelineData.yearMetaMap?.[word]?.[yr];
                if (isNorm && meta) {
                  const normVal = meta.normalized.toFixed(3).replace(/\.?0+$/, '');
                  const recStr = meta.totalRecords ? ` (${meta.raw} mentions / ${meta.totalRecords.toLocaleString()} records)` : ` (${meta.raw} mentions)`;
                  return ` #${word}: ${normVal} per 100 records${recStr}`;
                }
                return ` #${word}: ${item.formattedValue} mentions`;
              }
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
            ticks: {
              callback: (val) => isNorm ? `${val} / 100 rec` : val,
              precision: isNorm ? undefined : 0,
              font: { size: 12 }
            },
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
        onClick: (_event, elements, chart) => {
          if (!elements?.length) return;
          const index = elements[0].index;
          const clickedCat = chart.data.labels?.[index];
          if (clickedCat) {
            if (store.selectedCategory === clickedCat) {
              store.setCategory('All');
            } else {
              store.setCategory(clickedCat);
            }
          }
        },
        plugins: {
          legend: { position: 'top', labels: { font: { size: 13, weight: 'bold' } } },
          tooltip: {
            padding: 12,
            callbacks: {
              label: (item) => {
                const word = item.dataset.label || '';
                const cat = item.label;
                const meta = categoryData.catMetaMap?.[word]?.[cat];
                if (isNorm && meta) {
                  const normVal = meta.normalized.toFixed(3).replace(/\.?0+$/, '');
                  const recStr = meta.totalRecords ? ` (${meta.raw.toLocaleString()} mentions / ${meta.totalRecords.toLocaleString()} records)` : ` (${meta.raw.toLocaleString()} mentions)`;
                  return ` #${word}: ${normVal} per 100 records${recStr}`;
                }
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
            ticks: { callback: (val) => isNorm ? `${val} / 100 rec` : `${val}%`, font: { size: 12 } }
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
                const sent = item.label;
                const meta = sentimentData.sentMetaMap?.[word]?.[sent];
                if (isNorm && meta) {
                  const normVal = meta.normalized.toFixed(3).replace(/\.?0+$/, '');
                  const recStr = meta.totalRecords ? ` (${meta.raw.toLocaleString()} mentions / ${meta.totalRecords.toLocaleString()} records)` : ` (${meta.raw.toLocaleString()} mentions)`;
                  return ` #${word}: ${normVal} per 100 records${recStr}`;
                }
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
            ticks: { callback: (val) => isNorm ? `${val} / 100 rec` : `${val}%`, font: { size: 12 } }
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
  [() => store.getResults, () => store.getMetricMode, () => store.hasSearched],
  async () => {
    await nextTick();
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
  if (expandedChart.value === 'snippets') return '📖 Contextual Concept Snippets';
  return 'Expanded Chart';
});

const modalSubtitle = computed(() => {
  const isNorm = store.getMetricMode === 'normalized';
  if (expandedChart.value === 'timeline') {
    return isNorm
      ? 'Historical frequency rate per 100 archive records (1785–2008).'
      : 'Historical raw mention volume across 200+ years of criticism.';
  }
  if (expandedChart.value === 'category') {
    return isNorm
      ? 'Expressions per 100 records within each of the 9 primary cultural categories.'
      : 'Normalized percentage allocation across the 9 primary cultural categories.';
  }
  if (expandedChart.value === 'sentiment') {
    return isNorm
      ? 'Expressions per 100 records within each sentiment category.'
      : 'Comparative sentiment breakdown for all searched concepts.';
  }
  if (expandedChart.value === 'artist') {
    return 'Detailed breakdown of top artists critiqued with this aesthetic descriptor.';
  }
  if (expandedChart.value === 'snippets') {
    return 'Direct historical criticism excerpts with publication provenance and keyword highlighting.';
  }
  return '';
});
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
    <!-- Global Metric Mode Toggle & Information Banner -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white/95 backdrop-blur-md rounded-2xl border border-slate-200/90 p-4 shadow-sm">
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-lg shadow-sm transition-colors"
          :class="isNormalized ? 'bg-sky-50 text-sky-600 border border-sky-200' : 'bg-amber-50 text-amber-600 border border-amber-200'"
        >
          {{ isNormalized ? '⚡' : '📊' }}
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h2 class="text-sm font-bold text-slate-800">
              Metric Mode
            </h2>
            <span
              class="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold"
              :class="isNormalized ? 'bg-sky-50 text-sky-700 border border-sky-200' : 'bg-amber-50 text-amber-700 border border-amber-200'"
            >
              {{ isNormalized ? 'Normalized: expressions per 100 records' : 'Raw counts & percentage distribution' }}
            </span>
          </div>
          <p class="text-xs text-slate-500">
            {{ isNormalized
              ? 'Controlled for archive volume: rates calculated relative to all 294,550 criticism documents per year, category, and sentiment.'
              : 'Displays raw absolute mention counts and the proportion of mentions belonging to each category and sentiment.'
            }}
          </p>
        </div>
      </div>

      <!-- Segmented Toggle Control -->
      <div class="inline-flex items-center p-1 bg-slate-100/90 rounded-xl border border-slate-200 shadow-inner self-stretch sm:self-auto">
        <button
          @click="store.setMetricMode('normalized')"
          class="flex-1 sm:flex-initial px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5"
          :class="isNormalized ? 'bg-white text-sky-700 shadow-sm font-bold' : 'text-slate-500 hover:text-slate-800'"
        >
          <span>⚡ Expressions / 100 records</span>
        </button>
        <button
          @click="store.setMetricMode('raw')"
          class="flex-1 sm:flex-initial px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5"
          :class="!isNormalized ? 'bg-white text-slate-800 shadow-sm font-bold' : 'text-slate-500 hover:text-slate-800'"
        >
          <span>📊 Raw mentions &amp; %</span>
        </button>
      </div>
    </div>
    <!-- Empty State When Searched Concept Not Found -->
    <div
      v-if="store.hasSearched && !store.getResults.length && !store.isLoading"
      class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-12 text-center space-y-4 max-w-7xl mx-auto"
    >
      <div class="w-16 h-16 rounded-2xl bg-amber-50 text-amber-600 border border-amber-200 flex items-center justify-center text-3xl mx-auto shadow-sm">
        🔍
      </div>
      <div class="space-y-1.5 max-w-md mx-auto">
        <h3 class="text-base font-bold text-slate-800">
          No Analytics Available
        </h3>
        <p class="text-xs text-slate-500 leading-relaxed">
          No historical frequency or sentiment data was found for
          <strong class="text-slate-700 font-mono">{{ (store.words || []).map(w => `"${w}"`).join(', ') }}</strong> in the 273 curated aesthetic concepts.
        </p>
        <p class="text-[11px] text-slate-400">
          Check your spelling or choose from the curated suggestions above.
        </p>
      </div>
      <div class="pt-2">
        <button
          type="button"
          @click="store.resetSearch"
          class="text-xs font-semibold px-4 py-2 bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200 rounded-xl transition-colors shadow-sm"
        >
          Restore Sample Overview
        </button>
      </div>
    </div>

    <!-- Active Analytics Content (Charts & Snippets) -->
    <template v-else>
      <!-- Preview Note when viewing default sample demonstration data -->
      <div
        v-if="!store.hasSearched && !store.getResults.length"
        class="bg-sky-50/70 border border-sky-200/80 rounded-xl px-4 py-2.5 text-xs text-sky-800 flex items-center justify-between"
      >
        <div class="flex items-center gap-2">
          <span>💡</span>
          <span>
            <strong>Sample Preview Mode</strong> &mdash; Displaying demonstration baseline metrics for <code>#beautiful</code>. Search above to analyze any of the 273 curated concepts.
          </span>
        </div>
      </div>

      <!-- Grid of 4 Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 1. Timeline Chart -->
      <div class="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 space-y-4 relative group">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                <span>📈 Expression Timeline</span>
              </h3>
              <span
                v-if="store.hasActiveFilters"
                class="text-[10px] bg-sky-100 text-sky-800 px-2 py-0.5 rounded-full font-semibold border border-sky-200"
              >
                Filtered: {{ [store.selectedCategory !== 'All' ? store.selectedCategory : '', store.selectedArtist].filter(Boolean).join(' · ') }}
              </span>
            </div>
            <span class="text-xs text-slate-400">
              {{ isNormalized ? 'Rate per 100 records by year (1785–2008)' : 'Historical mentions by year (1785–2008)' }}
            </span>
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
            <div class="flex items-center gap-2">
              <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                <span>🎨 Artistic Categories</span>
              </h3>
              <span
                v-if="store.selectedCategory && store.selectedCategory !== 'All'"
                class="text-[10px] bg-sky-100 text-sky-800 px-2 py-0.5 rounded-full font-semibold border border-sky-200"
              >
                Focus: {{ store.selectedCategory }}
              </span>
            </div>
            <span class="text-xs text-slate-400">
              {{ isNormalized ? 'Rate per 100 records within each cultural category' : 'Distribution across 9 primary categories' }}
              <span class="text-slate-400 hidden sm:inline">&middot; Click any bar to filter</span>
            </span>
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
            <div class="flex items-center gap-2">
              <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                <span>💭 Sentiment Distribution</span>
              </h3>
              <span
                v-if="store.hasActiveFilters"
                class="text-[10px] bg-sky-100 text-sky-800 px-2 py-0.5 rounded-full font-semibold border border-sky-200"
              >
                Filtered
              </span>
            </div>
            <span class="text-xs text-slate-400">
              {{ isNormalized ? 'Rate per 100 records within each sentiment' : 'Positive, Neutral, Negative & Mixed' }}
            </span>
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
            <div class="flex items-center gap-2">
              <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                <span>🎭 Artist Associations &amp; Percentages</span>
              </h3>
              <span
                v-if="store.selectedArtist && store.selectedArtist.trim()"
                class="text-[10px] bg-sky-100 text-sky-800 px-2 py-0.5 rounded-full font-semibold border border-sky-200"
              >
                Filtered: {{ store.selectedArtist }}
              </span>
              <span
                v-else-if="store.selectedCategory && store.selectedCategory !== 'All'"
                class="text-[10px] bg-sky-100 text-sky-800 px-2 py-0.5 rounded-full font-semibold border border-sky-200"
              >
                Top in {{ store.selectedCategory }}
              </span>
            </div>
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
            <div class="flex items-center justify-between flex-wrap gap-2">
              <p class="text-xs font-bold text-slate-800">
                Snippets for {{ selectedArtist }} &middot; #{{ selectedWord }} ({{ selectedCount }} mentions{{ selectedPercentage ? ', ' + selectedPercentage : '' }})
              </p>
              <div class="flex items-center gap-2">
                <button
                  v-if="store.selectedArtist.toLowerCase() !== selectedArtist.toLowerCase()"
                  type="button"
                  @click="store.setArtist(selectedArtist)"
                  class="text-[11px] bg-sky-600 hover:bg-sky-500 text-white font-semibold px-2 py-0.5 rounded-md transition-colors shadow-xs"
                  title="Filter all analytical charts to this artist"
                >
                  Filter Analysis by {{ selectedArtist }}
                </button>
                <button
                  @click="selectedWord = ''"
                  class="text-[10px] text-slate-500 hover:text-slate-800 font-semibold"
                >
                  ✕ Clear
                </button>
              </div>
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
          <div class="flex items-center gap-2">
            <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
              <span>📖 Contextual Concept Snippets</span>
            </h3>
            <span
              v-if="store.hasActiveFilters"
              class="text-[10px] bg-sky-100 text-sky-800 px-2 py-0.5 rounded-full font-semibold border border-sky-200"
            >
              Filtered: {{ [store.selectedCategory !== 'All' ? store.selectedCategory : '', store.selectedArtist].filter(Boolean).join(' · ') }}
            </span>
          </div>
          <p class="text-xs text-slate-500">
            Representative sentences extracted from historical reviews where the searched concept appears.
          </p>
        </div>

        <div class="flex items-center gap-2 self-start sm:self-auto">
          <!-- Concept Switcher Tabs -->
          <div class="flex flex-wrap items-center gap-1.5">
            <button
              v-for="res in results"
              :key="res.Word"
              @click="activeConceptSnippetTab = res.Word"
              :class="[
                'text-xs font-semibold px-3 py-1 rounded-lg border transition-colors',
                activeConceptSnippetTab === res.Word
                  ? 'bg-amber-500 text-white border-amber-500 shadow-sm font-bold'
                  : 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200'
              ]"
            >
              #{{ res.Word }} ({{ res.TotalCount }})
            </button>
          </div>

          <!-- Maximize Button -->
          <button
            @click="openExpandModal('snippets')"
            class="text-xs text-slate-400 hover:text-slate-700 hover:bg-slate-100 p-1.5 rounded-lg transition-colors flex items-center gap-1 font-medium ml-1"
            title="Maximize View"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
            <span class="hidden sm:inline">Expand</span>
          </button>
        </div>
      </div>

      <!-- Snippets Display Grid -->
      <div v-if="activeConceptRecord" class="space-y-2">
        <div class="flex items-center justify-between text-xs text-slate-600">
          <span>Showing context snippets for <strong class="text-slate-900">#{{ activeConceptRecord.Word }}</strong>:</span>
          <div class="flex items-center gap-2">
            <span class="text-slate-400">{{ processedConceptSnippets.length }} samples</span>
            <button
              @click="toggleSnippetSort"
              class="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 transition-colors shadow-2xs"
              :title="snippetSortOrder === 'asc' ? 'Oldest first (1785 → 2008). Click to sort Newest first.' : 'Newest first (2008 → 1785). Click to sort Oldest first.'"
            >
              <span>{{ snippetSortOrder === 'asc' ? '⏳ Oldest first' : '⌛ Newest first' }}</span>
            </button>
          </div>
        </div>

        <div v-if="processedConceptSnippets.length" class="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-1">
          <div
            v-for="(snippet, sIdx) in processedConceptSnippets"
            :key="sIdx"
            class="bg-amber-50/60 hover:bg-amber-50/90 transition-colors p-3.5 rounded-xl border border-amber-200/70 text-xs text-slate-800 leading-relaxed flex flex-col justify-between space-y-2 shadow-xs"
          >
            <div>
              <!-- Metadata Header -->
              <div class="flex items-center justify-between gap-2 pb-2 mb-2 border-b border-amber-200/60 text-[11px]">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span class="text-[10px] text-amber-900 font-bold uppercase tracking-wider px-1.5 py-0.5 bg-amber-200/60 rounded">
                    Ex. {{ sIdx + 1 }}
                  </span>
                  <span
                    v-if="getSnippetEra(snippet)"
                    :class="['text-[10px] font-medium px-1.5 py-0.5 rounded border flex items-center gap-1', getEraBadgeInfo(getSnippetEra(snippet)).bg]"
                    :title="getEraBadgeInfo(getSnippetEra(snippet)).label"
                  >
                    <span>{{ getEraBadgeInfo(getSnippetEra(snippet)).icon }}</span>
                    <span>{{ getSnippetEra(snippet) }}</span>
                  </span>
                </div>
                <div class="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-slate-600 font-medium">
                  <span v-if="getSnippetPub(snippet)" class="inline-flex items-center gap-1 text-slate-700 font-semibold">
                    📰 {{ getSnippetPub(snippet) }}
                  </span>
                  <span v-if="getSnippetDate(snippet)" class="inline-flex items-center gap-1 text-slate-500 font-medium">
                    📅 {{ getSnippetDate(snippet) }}
                  </span>
                </div>
              </div>

              <!-- Snippet Sentence with Concept Highlight -->
              <p class="text-slate-800 font-serif italic text-[13px] leading-relaxed" v-html="highlightWord(getSnippetText(snippet), activeConceptRecord.Word)"></p>
            </div>

            <!-- Footer: Title / Author if available -->
            <div v-if="getSnippetTitle(snippet) || getSnippetAuthor(snippet)" class="pt-1.5 border-t border-amber-200/40 text-[10px] text-slate-400 flex items-center justify-between truncate gap-2">
              <span v-if="getSnippetTitle(snippet)" class="truncate" :title="getSnippetTitle(snippet)">“{{ getSnippetTitle(snippet) }}”</span>
              <span v-if="getSnippetAuthor(snippet)" class="shrink-0 font-medium text-slate-500">✍️ {{ getSnippetAuthor(snippet) }}</span>
            </div>
          </div>
        </div>

        <p v-else class="text-xs text-slate-400 italic p-4 text-center bg-slate-50 rounded-xl">
          No direct sentence snippets recorded for this concept.
        </p>
      </div>
    </div>
    </template>

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

          <div class="flex items-center gap-3">
            <!-- Modal Toggle for analytical charts -->
            <div v-if="expandedChart !== 'artist' && expandedChart !== 'snippets'" class="inline-flex items-center p-0.5 bg-slate-200/80 rounded-xl border border-slate-300/80 shadow-inner">
              <button
                @click="store.setMetricMode('normalized')"
                class="px-2.5 py-1 rounded-lg text-xs font-semibold transition-all"
                :class="isNormalized ? 'bg-white text-sky-700 shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'"
              >
                ⚡ / 100 rec
              </button>
              <button
                @click="store.setMetricMode('raw')"
                class="px-2.5 py-1 rounded-lg text-xs font-semibold transition-all"
                :class="!isNormalized ? 'bg-white text-slate-800 shadow-sm font-bold' : 'text-slate-600 hover:text-slate-900'"
              >
                📊 Raw / %
              </button>
            </div>

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
          <!-- Canvas for Timeline, Category, Sentiment, Artist charts -->
          <div v-if="expandedChart !== 'snippets'" class="h-[52vh] min-h-[380px] w-full relative">
            <canvas id="modal-chart-canvas"></canvas>
          </div>

          <!-- Snippets View for expandedChart === 'snippets' -->
          <div v-if="expandedChart === 'snippets'" class="space-y-4">
            <!-- Concept Switcher Tabs & Sorting in Modal -->
            <div class="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
              <div class="flex flex-wrap items-center gap-1.5">
                <button
                  v-for="res in results"
                  :key="res.Word"
                  @click="activeConceptSnippetTab = res.Word"
                  :class="[
                    'text-xs font-semibold px-3 py-1.5 rounded-lg border transition-colors',
                    activeConceptSnippetTab === res.Word
                      ? 'bg-amber-500 text-white border-amber-500 shadow-sm font-bold'
                      : 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200'
                  ]"
                >
                  #{{ res.Word }} ({{ res.TotalCount }})
                </button>
              </div>
              <div class="flex items-center gap-2">
                <span v-if="activeConceptRecord" class="text-xs text-slate-500">
                  Showing {{ processedConceptSnippets.length }} of {{ activeConceptRecord.ConceptSnippets?.length || 0 }} samples for <strong>#{{ activeConceptRecord.Word }}</strong>
                </span>
                <button
                  @click="toggleSnippetSort"
                  class="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors shadow-2xs"
                  :title="snippetSortOrder === 'asc' ? 'Oldest first (1785 → 2008). Click to sort Newest first.' : 'Newest first (2008 → 1785). Click to sort Oldest first.'"
                >
                  <span>{{ snippetSortOrder === 'asc' ? '⏳ Oldest first' : '⌛ Newest first' }}</span>
                </button>
              </div>
            </div>

            <!-- Historical Era Filter Bar in Modal -->
            <div class="flex items-center gap-1.5 overflow-x-auto pb-1">
              <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mr-1 shrink-0">Historical Era:</span>
              <button
                v-for="era in availableSnippetEras"
                :key="era.id"
                @click="activeSnippetEra = era.id"
                :disabled="era.count === 0 && era.id !== 'all'"
                :class="[
                  'text-xs px-2.5 py-1 rounded-lg border font-medium transition-colors flex items-center gap-1.5 shrink-0',
                  activeSnippetEra === era.id
                    ? 'bg-slate-800 text-white border-slate-800 shadow-sm font-semibold'
                    : era.count === 0
                      ? 'bg-slate-50 text-slate-300 border-slate-100 cursor-not-allowed'
                      : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'
                ]"
              >
                <span>{{ era.icon }}</span>
                <span>{{ era.label }}</span>
                <span :class="['text-[10px] px-1 rounded-full font-semibold', activeSnippetEra === era.id ? 'bg-slate-700 text-slate-200' : 'bg-slate-100 text-slate-500']">
                  {{ era.count }}
                </span>
              </button>
            </div>

            <!-- Snippet Grid in Modal (3 columns on large screens) -->
            <div v-if="processedConceptSnippets.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              <div
                v-for="(snippet, sIdx) in processedConceptSnippets"
                :key="sIdx"
                class="bg-amber-50/60 hover:bg-amber-50/90 transition-colors p-3.5 rounded-xl border border-amber-200/70 text-xs text-slate-800 leading-relaxed flex flex-col justify-between space-y-2 shadow-xs"
              >
                <div>
                  <div class="flex items-center justify-between gap-2 pb-2 mb-2 border-b border-amber-200/60 text-[11px]">
                    <div class="flex items-center gap-1.5 flex-wrap">
                      <span class="text-[10px] text-amber-900 font-bold uppercase tracking-wider px-1.5 py-0.5 bg-amber-200/60 rounded">
                        Ex. {{ sIdx + 1 }}
                      </span>
                      <span
                        v-if="getSnippetEra(snippet)"
                        :class="['text-[10px] font-medium px-1.5 py-0.5 rounded border flex items-center gap-1', getEraBadgeInfo(getSnippetEra(snippet)).bg]"
                        :title="getEraBadgeInfo(getSnippetEra(snippet)).label"
                      >
                        <span>{{ getEraBadgeInfo(getSnippetEra(snippet)).icon }}</span>
                        <span>{{ getSnippetEra(snippet) }}</span>
                      </span>
                    </div>
                    <div class="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-slate-600 font-medium">
                      <span v-if="getSnippetPub(snippet)" class="inline-flex items-center gap-1 text-slate-700 font-semibold">
                        📰 {{ getSnippetPub(snippet) }}
                      </span>
                      <span v-if="getSnippetDate(snippet)" class="inline-flex items-center gap-1 text-slate-500 font-medium">
                        📅 {{ getSnippetDate(snippet) }}
                      </span>
                    </div>
                  </div>
                  <p class="text-slate-800 font-serif italic text-[13px] leading-relaxed" v-html="highlightWord(getSnippetText(snippet), activeConceptRecord.Word)"></p>
                </div>
                <div v-if="getSnippetTitle(snippet) || getSnippetAuthor(snippet)" class="pt-1.5 border-t border-amber-200/40 text-[10px] text-slate-400 flex items-center justify-between truncate gap-2">
                  <span v-if="getSnippetTitle(snippet)" class="truncate" :title="getSnippetTitle(snippet)">“{{ getSnippetTitle(snippet) }}”</span>
                  <span v-if="getSnippetAuthor(snippet)" class="shrink-0 font-medium text-slate-500">✍️ {{ getSnippetAuthor(snippet) }}</span>
                </div>
              </div>
            </div>
            <p v-else class="text-xs text-slate-400 italic p-8 text-center bg-slate-50 rounded-xl">
              No direct sentence snippets recorded for this concept in the selected era.
            </p>
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
