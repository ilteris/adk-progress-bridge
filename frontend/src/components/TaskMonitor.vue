<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useAgentStream } from '../composables/useAgentStream'

const { state, runTool, stopTool, sendInput, reset, fetchTools: fetchToolsFromComposable, fetchHealth } = useAgentStream()
const auditDuration = ref(5)
const selectedTool = ref('long_audit')
const userInput = ref('')
const availableTools = ref<{ id: string, name: string }[]>([])
const showMetrics = ref(false)

const fetchTools = async () => {
  try {
    const toolsList = await fetchToolsFromComposable()
    availableTools.value = toolsList.map((id: string) => ({
      id,
      name: id.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
    }))
    if (availableTools.value.length > 0 && !availableTools.value.find(t => t.id === selectedTool.value)) {
      selectedTool.value = availableTools.value[0]?.id || ""
    }
  } catch (err) {
    console.error('Failed to fetch tools:', err)
    availableTools.value = [
      { id: 'long_audit', name: 'Audit Task' },
      { id: 'interactive_task', name: 'Interactive Task' }
    ]
  }
}

watch(() => state.useWS, () => {
  if (!state.isStreaming) {
    fetchTools()
  }
})

onMounted(() => {
  fetchTools()
  fetchHealth() // Initial fetch
})

const startTask = () => {
  const args = selectedTool.value === 'long_audit' ? { duration: auditDuration.value } : {}
  runTool(selectedTool.value, args)
}

const submitInput = () => {
  if (userInput.value.trim()) {
    sendInput(userInput.value)
    userInput.value = ''
  }
}

const handleReset = () => {
  reset()
  fetchHealth()
}

const formatBps = (bps: number) => {
    if (bps === undefined || bps === null) return '0 B/s'
    if (bps > 1024 * 1024) return (bps / (1024 * 1024)).toFixed(2) + ' MB/s'
    if (bps > 1024) return (bps / 1024).toFixed(2) + ' KB/s'
    return bps.toFixed(0) + ' B/s'
}
</script>

<template>
  <div class="container mt-2">
    <div class="card shadow-sm">
      <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
        <h4 class="mb-0">Task Monitor</h4>
        <div class="d-flex align-items-center gap-2">
          <button class="btn btn-sm btn-outline-light" @click="showMetrics = !showMetrics">
            {{ showMetrics ? 'Hide' : 'Show' }} Metrics
          </button>
          <span v-if="state.status === 'connected'" data-testid="status-badge" class="badge bg-success">Live ({{ state.useWS ? 'WS' : 'SSE' }})</span>
          <span v-else-if="state.status === 'waiting_for_input'" data-testid="status-badge" class="badge bg-warning text-dark">Awaiting Input</span>
          <span v-else-if="state.status === 'reconnecting'" data-testid="status-badge" class="badge bg-warning text-dark">
            <span class="spinner-border spinner-border-sm me-1" role="status"></span>
            Reconnecting...
          </span>
          <span v-else-if="state.status === 'connecting'" data-testid="status-badge" class="badge bg-info text-dark">Connecting...</span>
          <span v-else-if="state.status === 'error'" data-testid="status-badge" class="badge bg-danger">Error</span>
          <span v-else-if="state.status === 'completed'" data-testid="status-badge" class="badge bg-light text-dark">Done</span>
          <span v-else-if="state.status === 'cancelled'" data-testid="status-badge" class="badge bg-secondary">Cancelled</span>
        </div>
      </div>
      
      <div class="card-body">
        <!-- System Metrics Overlay/Panel -->
        <div v-if="showMetrics && state.systemMetrics" class="mb-4 p-3 border rounded bg-dark text-success font-monospace" style="font-size: 0.8rem;">
            <div class="row">
                <div class="col-md-3">
                    <strong>CPU:</strong> {{ state.systemMetrics.cpu_usage_percent?.toFixed(1) }}%<br>
                    <strong>Load:</strong> {{ state.systemMetrics.system_cpu_usage?.load_1m_percent?.toFixed(1) }}%
                </div>
                <div class="col-md-3">
                    <strong>Syscalls:</strong> {{ state.systemMetrics.system_cpu_stats?.syscall_rate_per_sec?.toFixed(0) }}/s<br>
                    <strong>SoftIRQ:</strong> {{ state.systemMetrics.system_cpu_stats?.soft_interrupt_rate_per_sec?.toFixed(0) }}/s
                </div>
                <div class="col-md-3">
                    <strong>WS Sent:</strong> {{ formatBps(state.systemMetrics.network_io_total?.sent_throughput_bps) }}<br>
                    <strong>WS Recv:</strong> {{ formatBps(state.systemMetrics.network_io_total?.recv_throughput_bps) }}
                </div>
                <div class="col-md-3">
                    <strong>Tasks:</strong> {{ state.systemMetrics.registry_size }} active<br>
                    <strong>Uptime:</strong> {{ Math.floor(state.systemMetrics.boot_time_seconds ? (Date.now()/1000 - state.systemMetrics.boot_time_seconds) : 0) }}s
                </div>
            </div>
        </div>

        <!-- Configuration Section -->
        <div class="mb-4 p-3 border rounded bg-body-tertiary">
          <h6>Task Configuration</h6>
          <div class="row g-3 align-items-center">
            <div class="col-md-4">
              <label for="toolSelect" class="form-label">Select Tool:</label>
              <select id="toolSelect" v-model="selectedTool" class="form-select" :disabled="state.isStreaming">
                <option v-for="tool in availableTools" :key="tool.id" :value="tool.id">
                  {{ tool.name }}
                </option>
              </select>
            </div>
            
            <div class="col-md-4" v-if="selectedTool === 'long_audit'">
              <label for="duration" class="form-label">Duration (seconds):</label>
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

            <div class="col-md-4 d-flex align-items-end">
              <div class="form-check form-switch mb-2">
                <input class="form-check-input" type="checkbox" id="useWS" v-model="state.useWS" :disabled="state.isStreaming">
                <label class="form-check-label" for="useWS">Use WebSockets</label>
              </div>
            </div>
          </div>
        </div>

        <!-- Interactive Input Section -->
        <div v-if="state.status === 'waiting_for_input'" class="mb-4 p-3 border border-warning rounded bg-warning-subtle animate-pulse">
          <h6>Agent Input Request</h6>
          <p class="mb-2"><strong>{{ state.inputPrompt }}</strong></p>
          <div class="input-group">
            <input 
              type="text" 
              v-model="userInput" 
              class="form-control" 
              placeholder="Type your response..."
              @keyup.enter="submitInput"
              autoFocus
            >
            <button class="btn btn-warning" @click="submitInput">Send Response</button>
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
          <div class="d-flex justify-content-between align-items-center mb-2"><h6>Log Console</h6><button class="btn btn-sm btn-link text-decoration-none" @click="state.logs = []" :disabled="state.isStreaming">Clear</button></div>
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
          @click="startTask" 
          class="btn btn-primary"
        >
          Start Task
        </button>
        <button 
          v-if="state.isStreaming"
          @click="stopTool" 
          class="btn btn-danger"
        >
          Stop Task
        </button>
        <button @click="handleReset" class="btn btn-outline-secondary" :disabled="state.isStreaming">
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

.font-monospace {
    font-family: 'Courier New', Courier, monospace;
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}
</style>