<script setup lang="ts">
import { useAgentStream } from '../composables/useAgentStream'

const { state, runTool, reset } = useAgentStream()

const startAudit = () => {
  runTool('long_audit', { duration: 5 })
}
</script>

<template>
  <div class="container mt-5">
    <div class="card shadow-sm">
      <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
        <h4 class="mb-0">ADK Progress Bridge</h4>
        <div v-if="state.isConnected" class="badge bg-success">Live</div>
      </div>
      
      <div class="card-body">
        <div class="mb-4">
          <label class="form-label d-flex justify-content-between">
            <span>{{ state.currentStep }}</span>
            <span>{{ state.progressPct }}%</span>
          </label>
          <div class="progress" style="height: 25px;">
            <div 
              class="progress-bar progress-bar-striped progress-bar-animated" 
              role="progressbar" 
              :style="{ width: state.progressPct + '%' }"
              :aria-valuenow="state.progressPct" 
              aria-valuemin="0" 
              aria-valuemax="100"
            ></div>
          </div>
        </div>

        <div class="mb-4">
          <h6>Log Console</h6>
          <div class="bg-dark text-light p-3 rounded" style="height: 200px; overflow-y: auto; font-family: monospace; font-size: 0.9rem;">
            <div v-for="(log, index) in state.logs" :key="index" class="mb-1">
              <span class="text-secondary">[{{ new Date().toLocaleTimeString() }}]</span> {{ log }}
            </div>
            <div v-if="state.logs.length === 0" class="text-secondary italic">No logs yet...</div>
          </div>
        </div>

        <div v-if="state.result" class="alert alert-success">
          <h6>Final Result:</h6>
          <pre class="mb-0">{{ JSON.stringify(state.result, null, 2) }}</pre>
        </div>

        <div v-if="state.error" class="alert alert-danger">
          <strong>Error:</strong> {{ state.error }}
        </div>
      </div>

      <div class="card-footer d-flex gap-2">
        <button 
          @click="startAudit" 
          class="btn btn-primary" 
          :disabled="state.isStreaming"
        >
          {{ state.isStreaming ? 'Running...' : 'Start Audit' }}
        </button>
        <button @click="reset" class="btn btn-outline-secondary" :disabled="state.isStreaming">
          Reset
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
