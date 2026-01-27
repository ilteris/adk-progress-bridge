<script setup lang="ts">
import { ref } from 'vue'
import { useAgentStream } from '../composables/useAgentStream'

const { state, runTool, stopTool, reset } = useAgentStream()
const auditDuration = ref(5)

const startAudit = () => {
  runTool('long_audit', { duration: auditDuration.value })
}
</script>

<template>
  <div class="container mt-2">
    <div class="card shadow-sm">
      <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
        <h4 class="mb-0">Task Monitor</h4>
        <div>
          <span v-if="state.status === 'connected'" class="badge bg-success">Live ({{ state.useWS ? 'WS' : 'SSE' }})</span>
          <span v-else-if="state.status === 'reconnecting'" class="badge bg-warning text-dark">
            <span class="spinner-border spinner-border-sm me-1" role="status"></span>
            Reconnecting...
          </span>
          <span v-else-if="state.status === 'connecting'" class="badge bg-info text-dark">Connecting...</span>
          <span v-else-if="state.status === 'error'" class="badge bg-danger">Error</span>
          <span v-else-if="state.status === 'completed'" class="badge bg-light text-dark">Done</span>
          <span v-else-if="state.status === 'cancelled'" class="badge bg-secondary">Cancelled</span>
        </div>
      </div>
      
      <div class="card-body">
        <!-- Configuration Section -->
        <div class="mb-4 p-3 border rounded bg-body-tertiary">
          <h6>Audit Configuration</h6>
          <div class="row g-3 align-items-center">
            <div class="col-auto">
              <label for="duration" class="col-form-label">Duration (seconds):</label>
            </div>
            <div class="col-auto">
              <input 
                type="number" 
                id="duration" 
                v-model.number="auditDuration" 
                class="form-control" 
                min="1" 
                max="60"
                :disabled="state.isStreaming"
              >
            </div>
            <div class="col-auto">
              <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" id="useWS" v-model="state.useWS" :disabled="state.isStreaming">
                <label class="form-check-label" for="useWS">Use WebSockets</label>
              </div>
            </div>
          </div>
        </div>

        <!-- Progress Bar Section -->
        <div class="mb-4">
          <label class="form-label d-flex justify-content-between">
            <span>{{ state.currentStep }}</span>
            <span>{{ state.progressPct }}%</span>
          </label>
          <div class="progress" style="height: 25px;">
            <div 
              class="progress-bar progress-bar-striped progress-bar-animated" 
              role="progressbar" 
              :style="{ 
                width: state.progressPct + '%',
                backgroundColor: state.status === 'reconnecting' ? '#ffc107' : (state.status === 'cancelled' ? '#6c757d' : '') 
              }"
              :aria-valuenow="state.progressPct" 
              aria-valuemin="0" 
              aria-valuemax="100"
            ></div>
          </div>
        </div>

        <!-- Log Console -->
        <div class="mb-4">
          <h6>Log Console</h6>
          <div class="bg-dark text-light p-3 rounded" style="height: 200px; overflow-y: auto; font-family: monospace; font-size: 0.9rem;">
            <div v-for="(log, index) in state.logs" :key="index" class="mb-1">
              <span class="text-secondary">[{{ new Date().toLocaleTimeString() }}]</span> {{ log }}
            </div>
            <div v-if="state.logs.length === 0" class="text-secondary italic">No logs yet...</div>
          </div>
        </div>

        <!-- Result/Error Section -->
        <div v-if="state.result" class="alert alert-success mt-3">
          <h6>Final Result:</h6>
          <pre class="mb-0 text-dark-emphasis">{{ JSON.stringify(state.result, null, 2) }}</pre>
        </div>

        <div v-if="state.error" class="alert alert-danger mt-3">
          <strong>Error:</strong> {{ state.error }}
        </div>
      </div>

      <div class="card-footer d-flex gap-2">
        <button 
          v-if="!state.isStreaming"
          @click="startAudit" 
          class="btn btn-primary"
        >
          Start Audit
        </button>
        <button 
          v-if="state.isStreaming"
          @click="stopTool" 
          class="btn btn-danger"
        >
          Stop Task
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