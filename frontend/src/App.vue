<script setup lang="ts">
import { ref } from 'vue'
import TaskMonitor from './components/TaskMonitor.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import 'bootstrap/dist/css/bootstrap.min.css'

const monitors = ref([1])
const nextId = ref(2)
const version = "1.7.5"

const addMonitor = () => {
  monitors.value.push(nextId.value++)
}

const removeMonitor = (id: number) => {
  if (monitors.value.length > 1) {
    monitors.value = monitors.value.filter(m => m !== id)
  }
}
</script>

<template>
  <nav class="navbar border-bottom shadow-sm mb-4">
    <div class="container">
      <div class="d-flex align-items-center gap-2">
        <span class="navbar-brand mb-0 h1">ADK Bridge</span>
        <span class="badge bg-secondary opacity-75" style="font-size: 0.7rem;">v{{ version }}</span>
      </div>
      <div class="d-flex align-items-center gap-3">
        <button @click="addMonitor" class="btn btn-sm btn-outline-primary">
          + Add Monitor
        </button>
        <ThemeToggle />
      </div>
    </div>
  </nav>
  <main class="container py-3">
    <div class="row g-4">
      <div v-for="id in monitors" :key="id" class="col-12 col-xl-6">
        <div class="position-relative">
          <button 
            v-if="monitors.length > 1"
            @click="removeMonitor(id)" 
            class="btn btn-close position-absolute top-0 end-0 m-2 z-3" 
            aria-label="Close"
          ></button>
          <TaskMonitor />
        </div>
      </div>
    </div>
  </main>
</template>

<style>
.btn-close {
  background-color: rgba(255, 255, 255, 0.8);
  padding: 0.5rem;
  border-radius: 50%;
}
[data-bs-theme='dark'] .btn-close {
  filter: invert(1) grayscale(100%) brightness(200%);
}
</style>