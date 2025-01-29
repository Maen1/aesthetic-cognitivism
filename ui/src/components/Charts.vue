<script setup>
import { useWordStore } from '../stores/WordStore';
import { ref, watch  ,onMounted, computed } from 'vue';
import Chart from 'chart.js/auto';

const store = useWordStore()

let chart1, chart2, chart3


const results = computed(() => store.getResults)



onMounted(() => {
let ctx1 = document.getElementById("line");
 let config1 =  {
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
  };

  
let ctx2 = document.getElementById('bar');
let config2 = {
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
  };
  let ctx3 = document.getElementById('pie');
let config3 = {
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
  };  


  chart1 = new Chart(ctx1, config1)
  chart2 = new Chart(ctx2, config2)
  chart3 = new Chart(ctx3, config3)

})



watch(() => store.getResults,
    ()=> {
    console.log("length", store.getWordsLength)
    console.log("words", store.getResults[0]["YearCounts"]["year"])
    let all_years = new Set();
    // Collect all unique years
    store.getResults.forEach(result => {
        result.YearCounts.forEach(item => all_years.add(item.year));
    });

    // Convert Set to sorted array for labels
    let labels = Array.from(all_years).sort((a, b) => a - b);

    // Create datasets array
    let datasets = store.getResults.map(result => {
        return {
            label: result.Word,  // Use the word as the label
            data: labels.map(year => {
                let entry = result.YearCounts.find(item => item.year === year);
                return entry ? entry.count : 0; // Fill missing years with 0
            }),
            fill: false,
            borderColor: getRandomColor(),
            backgroundColor: getRandomColor(0.2),
            tension: 0.1
        };
    });

    console.log("Datasets:", datasets);
    console.log("Labels:", labels);

    for(const res of store.getResults){
        console.log("from loop", res["Word"])
      }
    let ctx1 = document.getElementById("line");
    let config1 =  {
          type: 'line',
          data :{
            labels,
            datasets,
          }
      };
    function getRandomColor(alpha = 1) {
    const r = Math.floor(Math.random() * 255);
    const g = Math.floor(Math.random() * 255);
    const b = Math.floor(Math.random() * 255);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
      
    let ctx2 = document.getElementById('bar');
    let config2 = {
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
      };
      let ctx3 = document.getElementById('pie');
    let config3 = {
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
      };  

    if(chart1){
      chart1.destroy()
      chart2.destroy()
      chart3.destroy()
      chart1 = new Chart(ctx1, config1)
      chart2 = new Chart(ctx2, config2)
      chart3 = new Chart(ctx3, config3)
    }else{
      chart1 = new Chart(ctx1, config1)
      chart2 = new Chart(ctx2, config2)
      chart3 = new Chart(ctx3, config3)
    }
    
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
