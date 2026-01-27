import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  // @ts-ignore
  test: {
    environment: 'jsdom',
    globals: true,
  },
})