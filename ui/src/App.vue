<script setup>
import { ref } from 'vue';
import SearchForm from './components/SearchForm.vue';
import Charts from './components/Charts.vue';
import CriticismExplorer from './components/CriticismExplorer.vue';

const activeTab = ref('analytics'); // 'analytics' | 'explorer'
</script>

<template>
  <div class="min-h-screen bg-slate-100 text-slate-900 flex flex-col">
    <!-- Main Header -->
    <header class="bg-slate-900 text-white shadow-md sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between py-4 gap-4">
          <!-- Logo & Title -->
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-fuchsia-600 to-sky-500 flex items-center justify-center font-bold text-xl text-white shadow-inner">
              ✨
            </div>
            <div>
              <h1 class="text-xl font-bold tracking-tight text-white leading-tight">
                Aesthetic Cognitivism
              </h1>
              <p class="text-xs text-slate-400 font-medium">
                Digital Humanities Art & Culture Criticism Analytics
              </p>
            </div>
          </div>

          <!-- Navigation Tabs -->
          <nav class="flex items-center bg-slate-800/80 p-1.5 rounded-xl border border-slate-700/60 self-start sm:self-auto">
            <button
              @click="activeTab = 'analytics'"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all',
                activeTab === 'analytics'
                  ? 'bg-sky-600 text-white shadow'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              ]"
            >
              <span>📊 Word Analytics</span>
            </button>

            <button
              @click="activeTab = 'explorer'"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all',
                activeTab === 'explorer'
                  ? 'bg-sky-600 text-white shadow'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              ]"
            >
              <span>📰 Criticism Explorer</span>
            </button>
          </nav>
        </div>
      </div>
    </header>

    <!-- Main Content Body -->
    <main class="flex-1 pb-16">
      <!-- Tab 1: Word Analytics -->
      <section v-show="activeTab === 'analytics'" class="space-y-6">
        <SearchForm />
        <Charts />
      </section>

      <!-- Tab 2: Criticism Explorer -->
      <section v-show="activeTab === 'explorer'">
        <CriticismExplorer />
      </section>
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
      <div class="max-w-7xl mx-auto px-4">
        Aesthetic Cognitivism &middot; Centre for Digital Humanities Uppsala (CDHU) &middot; Powered by FastAPI & Vue 3
      </div>
    </footer>
  </div>
</template>

<style>
/* Smooth base transitions */
html {
  scroll-behavior: smooth;
}
</style>
