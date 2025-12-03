<script setup>
	import { useWordStore } from '../stores/WordStore';
	import { ref, watch, onMounted, computed } from 'vue';
	import Chart, { scales } from 'chart.js/auto';

	const store = useWordStore();

	let chart1, chart2, chart3, chart4, chart5;

	const results = computed(() => store.getResults);

	onMounted(() => {
		let ctx1 = document.getElementById('line');
		let config1 = {
			type: 'line',
			data: {
				labels: [1980, 1981, 1982, 1983, 1990, 1991, 1995],
				datasets: [
					{
						label: 'beautiful',
						data: [65, 59, 80, 81, 56, 55, 40],
						fill: false,
						borderColor: 'rgb(75, 192, 192)',
						backgroundColor: 'rgba(75, 192, 192, 0.2)',
						tension: 0.1,
					},
					{
						label: 'profound',
						data: [6, 59, 70, 31, 36, 55, 0],
						fill: false,
						borderColor: 'rgb(192, 75, 192)',
						backgroundColor: 'rgba(192, 75, 192, 0.2)',
						tension: 0.1,
					},
				],
			},
		};

		let ctx2 = document.getElementById('bar-category');
		let config2 = {
			type: 'bar',
			data: {
				labels: [
					'Poetry',
					'Concerts',
					'Theater',
					'Dance',
					'Exhibitions',
					'Operas',
					'Dance',
					'Movies',
				],
				datasets: [
					{
						label: 'Beautiful',
						data: [12, 19, 20, 5, 8, 3, 6, 1],
						backgroundColor: [
							'rgba(255, 99, 132, 0.2)',
							'rgba(54, 162, 235, 0.2)',
							'rgba(255, 206, 86, 0.2)',
							'rgba(75, 192, 192, 0.2)',
							'rgba(153, 102, 255, 0.2)',
							'rgba(255, 159, 64, 0.2)',
							'rgba(255, 15, 64, 0.2)',
							'rgba(25, 159, 64, 0.2)',
						],
						borderColor: [
							'rgba(255, 99, 132, 1)',
							'rgba(54, 162, 235, 1)',
							'rgba(255, 206, 86, 1)',
							'rgba(75, 192, 192, 1)',
							'rgba(153, 102, 255, 1)',
							'rgba(255, 159, 64, 1)',
							'rgba(255, 15, 64, 1)',
							'rgba(25, 159, 64, 1)',
						],
						borderWidth: 1,
					},
					{
						label: 'profound',
						data: [12, 1, 10, 15, 4, 3, 12, 20],
						backgroundColor: [
							'rgba(255, 99, 132, 0.2)',
							'rgba(54, 162, 235, 0.2)',
							'rgba(255, 206, 86, 0.2)',
							'rgba(75, 192, 192, 0.2)',
							'rgba(153, 102, 255, 0.2)',
							'rgba(255, 159, 64, 0.2)',
							'rgba(255, 15, 64, 0.2)',
							'rgba(25, 159, 64, 0.2)',
						],
						borderColor: [
							'rgba(255, 99, 132, 1)',
							'rgba(54, 162, 235, 1)',
							'rgba(255, 206, 86, 1)',
							'rgba(75, 192, 192, 1)',
							'rgba(153, 102, 255, 1)',
							'rgba(255, 159, 64, 1)',
							'rgba(255, 15, 64, 1)',
							'rgba(25, 159, 64, 1)',
						],
						borderWidth: 1,
					},
				],
			},
			options: {
				scales: {
					y: {
						beginAtZero: true,
					},
				},
			},
		};

		let ctx4 = document.getElementById('bar-concept');
		let config4 = {
			type: 'bar',
			data: {
				labels: [
					'Cognitive',
					'Evaluative',
					'Mimetic',
					'Aesthetic',
					'Emotion',
					'Visual',
				],
				datasets: [
					{
						label: 'Beautiful',
						data: [12, 19, 20, 5, 8, 3],
						backgroundColor: [
							'rgba(255, 99, 132, 0.2)',
							'rgba(54, 162, 235, 0.2)',
							'rgba(255, 206, 86, 0.2)',
							'rgba(75, 192, 192, 0.2)',
							'rgba(153, 102, 255, 0.2)',
							'rgba(255, 159, 64, 0.2)',
						],
						borderColor: [
							'rgba(255, 99, 132, 1)',
							'rgba(54, 162, 235, 1)',
							'rgba(255, 206, 86, 1)',
							'rgba(75, 192, 192, 1)',
							'rgba(153, 102, 255, 1)',
							'rgba(255, 159, 64, 1)',
						],
						borderWidth: 1,
					},
					{
						label: 'profound',
						data: [12, 1, 10, 15, 4, 3],
						backgroundColor: [
							'rgba(255, 99, 132, 0.2)',
							'rgba(54, 162, 235, 0.2)',
							'rgba(255, 206, 86, 0.2)',
							'rgba(75, 192, 192, 0.2)',
							'rgba(153, 102, 255, 0.2)',
							'rgba(255, 159, 64, 0.2)',
						],
						borderColor: [
							'rgba(255, 99, 132, 1)',
							'rgba(54, 162, 235, 1)',
							'rgba(255, 206, 86, 1)',
							'rgba(75, 192, 192, 1)',
							'rgba(153, 102, 255, 1)',
							'rgba(255, 159, 64, 1)',
						],
						borderWidth: 1,
					},
				],
			},
			options: {
				scales: {
					y: {
						beginAtZero: true,
					},
				},
			},
		};

		let ctx5 = document.getElementById('bar-sentiment');
		let config5 = {
			type: 'bar',
			data: {
				labels: ['Positive', 'Negative', 'Neutral'],
				datasets: [
					{
						label: 'Beautiful',
						data: [12, 1, 20],
						backgroundColor: [
							'rgba(255, 99, 132, 0.2)',
							'rgba(54, 162, 235, 0.2)',
							'rgba(255, 206, 86, 0.2)',
							'rgba(75, 192, 192, 0.2)',
							'rgba(153, 102, 255, 0.2)',
							'rgba(255, 159, 64, 0.2)',
						],
						borderColor: [
							'rgba(255, 99, 132, 1)',
							'rgba(54, 162, 235, 1)',
							'rgba(255, 206, 86, 1)',
							'rgba(75, 192, 192, 1)',
							'rgba(153, 102, 255, 1)',
							'rgba(255, 159, 64, 1)',
						],
						borderWidth: 1,
					},
					{
						label: 'profound',
						data: [12, 1, 3],
						backgroundColor: [
							'rgba(255, 99, 132, 0.2)',
							'rgba(54, 162, 235, 0.2)',
							'rgba(255, 206, 86, 0.2)',
						],
						borderColor: [
							'rgba(255, 99, 132, 1)',
							'rgba(54, 162, 235, 1)',
							'rgba(255, 206, 86, 1)',
						],
						borderWidth: 1,
					},
				],
			},
			options: {
				scales: {
					y: {
						beginAtZero: true,
					},
				},
			},
		};

		let ctx3 = document.getElementById('pie');
		let config3 = {
			type: 'doughnut',
			data: {
				labels: ['Mozart', 'Beethoven', 'Bach'],
				datasets: [
					{
						label: 'Dataset',
						data: [30, 5, 10],
						backgroundColor: [
							'rgb(255, 99, 132)',
							'rgb(54, 162, 235)',
							'rgb(255, 205, 86)',
						],
						hoverOffset: 4,
					},
				],
			},
		};

		chart1 = new Chart(ctx1, config1);
		chart2 = new Chart(ctx2, config2);
		chart3 = new Chart(ctx3, config3);
		chart4 = new Chart(ctx4, config4);
		chart5 = new Chart(ctx5, config5);
	});

	watch(
		() => store.getResults,
		() => {
			let all_years = new Set();
			// Collect all unique years
			store.getResults.forEach((result) => {
				result.YearCounts.forEach((item) => all_years.add(item.year));
			});

			// Convert Set to sorted array for labels
			let line_labels = Array.from(all_years).sort((a, b) => a - b);

			// Create datasets array
			let line_datasets = store.getResults.map((result, index) => {
				return {
					label: result.Word, // Use the word as the label
					data: line_labels.map((year) => {
						let entry = result.YearCounts.find((item) => item.year === year);
						return entry ? entry.count : 0; // Fill missing years with 0
					}),
					fill: false,
					borderColor: getRandomColor(index),
					backgroundColor: getRandomColor(index, 0.2),
					tension: 0.1,
				};
			});

			let maxValue = [...line_datasets.flatMap((dataset) => dataset.data)].sort(
				(a, b) => b - a
			)[1];

			// Categories

			let all_categories = new Set();
			store.getResults.forEach((result) => {
				result.CategoryCounts.forEach((item) =>
					all_categories.add(item.category)
				);
			});

			let category_labels = Array.from(all_categories).sort((a, b) => a - b);
			// Create datasets array
			let category_datasets = store.getResults.map((result, index) => {
				return {
					label: result.Word, // Use the word as the label
					data: category_labels.map((category) => {
						let entry = result.CategoryCounts.find(
							(item) => item.category === category
						);
						return entry ? entry.count : 0; // Fill missing years with 0
					}),
					borderColor: getRandomColor(index),
					backgroundColor: getRandomColor(index, 0.2),
					borderWidth: 1,
				};
			});

			//Concepts
			let all_concepts = new Set();
			store.getResults.forEach((result) => {
				result.ConceptCounts.forEach((item) => all_concepts.add(item.concept));
			});

			let concept_labels = Array.from(all_concepts).sort((a, b) => a - b);
			// Create datasets array
			let concept_datasets = store.getResults.map((result, index) => {
				return {
					label: result.Word, // Use the word as the label
					data: concept_labels.map((concept) => {
						let entry = result.ConceptCounts.find(
							(item) => item.concept === concept
						);
						return entry ? entry.count : 0; // Fill missing years with 0
					}),
					borderColor: getRandomColor(index),
					backgroundColor: getRandomColor(index, 0.2),
					borderWidth: 1,
				};
			});

			//Sentiment
			let all_sentiments = new Set();
			store.getResults.forEach((result) => {
				result.SentimentCounts.forEach((item) =>
					all_sentiments.add(item.sentiment)
				);
			});

			let sentiment_labels = Array.from(all_sentiments).sort((a, b) => a - b);
			// Create datasets array
			let sentiment_datasets = store.getResults.map((result, index) => {
				return {
					label: result.Word, // Use the word as the label
					data: sentiment_labels.map((sentiment) => {
						let entry = result.SentimentCounts.find(
							(item) => item.sentiment === sentiment
						);
						return entry ? entry.count : 0; // Fill missing years with 0
					}),
					borderColor: getRandomColor(index),
					backgroundColor: getRandomColor(index, 0.2),
					borderWidth: 1,
				};
			});

			let all_artists = new Set();
			// Collect all unique years
			store.getResults.forEach((result) => {
				result.ArtistCounts.forEach((item) => all_artists.add(item.artist));
			});

			let donut_labels = Array.from(all_artists).sort((a, b) => a - b);

			// Create datasets array
			let donut_datasets = store.getResults.map((result, index) => {
				return {
					label: result.Word, // Use the word as the label
					data: donut_labels.map((artist) => {
						let entry = result.ArtistCounts.find(
							(item) => item.artist === artist
						);
						return entry ? entry.count : 0; // Fill missing years with 0
					}),
					borderColor: getRandomColor(index),
					backgroundColor: getRandomColor(index, 0.2),
					hoverOffset: 4,
				};
			});

			function seededRandom(seed) {
				let x = Math.sin(seed) * 10000;
				return x - Math.floor(x);
			}

			function getRandomColor(seed, alpha = 1) {
				const r = Math.floor(seededRandom(seed + 10) * 255);
				const g = Math.floor(seededRandom(seed + 11) * 255);
				const b = Math.floor(seededRandom(seed + 12) * 255);

				return `rgba(${r}, ${g}, ${b}, ${alpha})`;
			}

			let ctx1 = document.getElementById('line');
			let config1 = {
				type: 'line',
				data: {
					labels: line_labels,
					datasets: line_datasets,
				},
				options: {
					scales: {
						y: {
							max: maxValue + 100,
						},
					},
					responsive: true,
				},
			};

			let ctx2 = document.getElementById('bar-category');
			let config2 = {
				type: 'bar',
				data: {
					labels: category_labels,
					datasets: category_datasets,
				},
				options: {
					scales: {
						y: {
							beginAtZero: true,
						},
					},
				},
			};

			let ctx4 = document.getElementById('bar-concept');
			let config4 = {
				type: 'bar',
				data: {
					labels: concept_labels,
					datasets: concept_datasets,
				},
				options: {
					scales: {
						y: {
							beginAtZero: true,
						},
					},
				},
			};

			let ctx5 = document.getElementById('bar-sentiment');
			let config5 = {
				type: 'bar',
				data: {
					labels: sentiment_labels,
					datasets: sentiment_datasets,
				},
				options: {
					scales: {
						y: {
							beginAtZero: true,
						},
					},
				},
			};
			let ctx3 = document.getElementById('pie');
			let config3 = {
				type: 'doughnut',
				data: {
					labels: donut_labels,
					datasets: donut_datasets,
				},
			};

			if (chart1) {
				chart1.destroy();
				chart2.destroy();
				chart3.destroy();
				chart4.destroy();
				chart5.destroy();

				chart1 = new Chart(ctx1, config1);
				chart2 = new Chart(ctx2, config2);
				chart3 = new Chart(ctx3, config3);
				chart4 = new Chart(ctx4, config4);
				chart5 = new Chart(ctx5, config5);
			} else {
				chart1 = new Chart(ctx1, config1);
				chart2 = new Chart(ctx2, config2);
				chart3 = new Chart(ctx3, config3);
				chart4 = new Chart(ctx4, config4);
				chart5 = new Chart(ctx5, config5);
			}
		}
	);

	// Search state
	const searchTerm = ref('');
	let words = ref('');
	// Define the function to send the search to GraphQL API

	const searchExpressions = async () => {
		store.setSearchTerm(searchTerm);
		store.searchExpressions();
	};
</script>

<template>
	<div class="bg-slate-50 p-5 rounded-xl my-5">
		<p class="text-xl">Expression Timeline</p>
		<canvas id="line"></canvas>
	</div>
	<div class="bg-slate-50 p-5 rounded-xl my-5">
		<p class="text-xl">Artistic Categories</p>
		<canvas id="bar-category"></canvas>
	</div>

	<!---
	<div class="bg-slate-50 p-5 rounded-xl my-5">
		<p class="text-xl">Concepts Categories</p>
		<canvas id="bar-concept"></canvas>
	</div>

	-->

	<div class="bg-slate-50 p-5 rounded-xl my-5">
		<p class="text-xl">Sentiment Analysis</p>
		<canvas id="bar-sentiment"></canvas>
	</div>
	<div class="bg-slate-50 p-5 rounded-xl my-5">
		<p class="text-xl">Artist</p>
		<canvas id="pie"></canvas>
	</div>
</template>
