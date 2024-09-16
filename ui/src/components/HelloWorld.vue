<script setup>
import { useCounterStore } from '../stores/ChartStore';
import { ref } from 'vue'

const store = useCounterStore()


defineProps({
  msg: String,
})

</script>

<template>
  <div class="w-full bg-fuchsia-300 p-4 flex justify-center rounded my-2">
      <h1 class="text-xl font-bold ">{{ msg }}</h1>
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
