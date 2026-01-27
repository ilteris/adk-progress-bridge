<script setup lang="ts">
import { ref, onMounted } from 'vue'

const isDark = ref(false)

const toggleTheme = () => {
  isDark.value = !isDark.value
  const theme = isDark.value ? 'dark' : 'light'
  document.documentElement.setAttribute('data-bs-theme', theme)
  localStorage.setItem('theme', theme)
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  
  if (savedTheme) {
    isDark.value = savedTheme === 'dark'
  } else {
    isDark.value = systemDark
  }
  
  document.documentElement.setAttribute('data-bs-theme', isDark.value ? 'dark' : 'light')
})
</script>

<template>
  <button 
    @click="toggleTheme" 
    class="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1"
    :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
  >
    <template v-if="isDark">
      <span class="bi bi-sun-fill"></span>
      <span>Light</span>
    </template>
    <template v-else>
      <span class="bi bi-moon-fill"></span>
      <span>Dark</span>
    </template>
  </button>
</template>

<style scoped>
/* Bootstrap icons can be added via CDN in index.html if needed, 
   but for now we'll use simple text or emojis if icons aren't available */
</style>