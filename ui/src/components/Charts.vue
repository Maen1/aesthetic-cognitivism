<script setup>
import { useWordStore } from '../stores/WordStore';
import { ref,  onMounted } from 'vue';
import Chart from 'chart.js/auto';

const store = useWordStore()


onMounted(() => {
    const ctx = document.getElementById('bar');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Poetry', 'Concerts', 'Theater', 'Dance', 'Exhibitions', 'Operas'],
            datasets: [{
                label: 'Beautiful',
                data: [12, 19, 20, 5, 8, 3],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                borderWidth: 1
            },{
                label: 'profound',
                data: [12, 1, 10, 15, 4, 3],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
    const ctx2 = document.getElementById('pie');
    new Chart(ctx2, {
        type: 'doughnut',
        data: {
            labels: [
                'Mozart',
                'Beethoven',
                'Bach'
            ],
            datasets: [{
                label: 'Dataset',
                data: [30, 5, 10],
                backgroundColor: [
                'rgb(255, 99, 132)',
                'rgb(54, 162, 235)',
                'rgb(255, 205, 86)'
                ],
                hoverOffset: 4
            }]
        }
    });  

    const ctx3 = document.getElementById("line");
    new Chart(ctx3, {
        type: 'line',
        data :{
            labels:  [1980, 1981, 1982, 1983, 1990, 1991, 1995],
            datasets: [{
                label: 'beautiful',
                data: [65, 59, 80, 81, 56, 55, 40],
                fill: false,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            },
            {
                label: 'profound',
                data: [6, 59, 70, 31, 36, 55, 0],
                fill: false,
                borderColor: 'rgb(192, 75, 192)',
                backgroundColor: 'rgba(192, 75, 192, 0.2)',
                tension: 0.1
            }]
        }
    });
})


// Search state
const searchTerm = ref('');
let words = ref('')
// Define the function to send the search to GraphQL API

const searchExpressions = async () => {
  store.setSearchTerm(searchTerm)
  console.log(store.searchTerm)
  store.searchExpressions()
};

</script>

<template>
    <div class="bg-slate-50 p-5 rounded-xl my-5">
        <p class="text-xl">Expression Timeline</p>
        <canvas id="line"></canvas>
    </div>
    <div class="bg-slate-50 p-5 rounded-xl my-5">
        <p class="text-xl">Categories</p>
        <canvas id="bar"></canvas>
    </div>
    <div class="bg-slate-50 p-5 rounded-xl my-5">
        <p class="text-xl">Authors</p>
        <canvas id="pie"></canvas>
    </div>
      

</template>
