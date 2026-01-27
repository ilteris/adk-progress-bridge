<script setup lang="ts">
import TaskMonitor from './components/TaskMonitor.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import 'bootstrap/dist/css/bootstrap.min.css'
</script>

<template>
  <nav class="navbar border-bottom shadow-sm mb-4">
    <div class="container">
      <span class="navbar-brand mb-0 h1">ADK Bridge</span>
      <ThemeToggle />
    </div>
  </nav>
  <main class="min-vh-100 py-3">
    <TaskMonitor />
  </main>
</template>

<style>
/* Remove the hardcoded body background from style.css or App.vue 
   and let Bootstrap's theme handles it */
</style>