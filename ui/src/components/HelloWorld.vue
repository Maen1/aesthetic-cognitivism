<script setup>
import { useCounterStore } from '../stores/ChartStore';
import { ref } from 'vue'

const store = useCounterStore()


defineProps({
  msg: String,
})

</script>

<template>
  <div class="w-full bg-fuchsia-700 p-4 flex justify-center rounded">
      <h1 class="text-2xl font-bold text-slate-100">{{ msg }}</h1>
  </div>

<!-- 
  <div class="card">
    <button class="bg-slate-100 rounded-full p-2" @click="store.increment">count is {{ store.doubleCount }}</button>
  </div> -->
</template>

<style scoped>
.read-the-docs {
  color: #888;
}
</style>
