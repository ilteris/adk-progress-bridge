import { reactive } from 'vue'

interface ProgressPayload {
  step: string
  pct: number
  log?: string
  metadata?: Record<string, any>
}

interface AgentEvent {
  call_id: string
  type: 'progress' | 'result' | 'error'
  payload: any
}

export type ConnectionStatus = 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'error' | 'completed'

export interface AgentState {
  status: ConnectionStatus
  isConnected: boolean
  callId: string | null
  currentStep: string
  progressPct: number
  logs: string[]
  result: any | null
  error: string | null
  isStreaming: boolean
}

// Support VITE_API_URL environment variable, defaulting to localhost for dev
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
// Support VITE_BRIDGE_API_KEY for authenticated requests
const BRIDGE_API_KEY = import.meta.env.VITE_BRIDGE_API_KEY || ''

export function useAgentStream() {
  const state = reactive<AgentState>({
    status: 'idle',
    isConnected: false,
    callId: null,
    currentStep: 'Idle',
    progressPct: 0,
    logs: [],
    result: null,
    error: null,
    isStreaming: false
  })

  const reset = () => {
    state.status = 'idle'
    state.isConnected = false
    state.callId = null
    state.currentStep = 'Idle'
    state.progressPct = 0
    state.logs = []
    state.result = null
    state.error = null
    state.isStreaming = false
  }

  const runTool = async (toolName: string, args: Record<string, any> = {}) => {
    reset()
    state.isStreaming = true
    state.status = 'connecting'

    try {
      // 1. Start Task
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (BRIDGE_API_KEY) {
        headers['X-API-Key'] = BRIDGE_API_KEY
      }

      const response = await fetch(`${API_BASE_URL}/start_task/${toolName}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(args)
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to start task: ${response.statusText}`)
      }
      
      const { call_id } = await response.json()
      state.callId = call_id

      // 2. Connect to SSE
      // Add api_key to query params if available
      const streamUrl = new URL(`${API_BASE_URL}/stream/${call_id}`)
      if (BRIDGE_API_KEY) {
        streamUrl.searchParams.append('api_key', BRIDGE_API_KEY)
      }

      const eventSource = new EventSource(streamUrl.toString())

      eventSource.onopen = () => {
        state.isConnected = true
        state.status = 'connected'
        state.error = null // Clear any previous transient errors
        state.logs.push('Connected to stream...')
      }

      eventSource.onmessage = (event) => {
        const data: AgentEvent = JSON.parse(event.data)
        
        if (data.type === 'progress') {
          const payload = data.payload as ProgressPayload
          state.currentStep = payload.step
          state.progressPct = payload.pct
          if (payload.log) state.logs.push(payload.log)
        } else if (data.type === 'result') {
          state.result = data.payload
          state.currentStep = 'Completed'
          state.progressPct = 100
          state.status = 'completed'
          state.logs.push('Task completed successfully.')
          eventSource.close()
          state.isStreaming = false
        } else if (data.type === 'error') {
          state.error = data.payload.detail || 'Unknown error'
          state.status = 'error'
          state.logs.push(`Error: ${state.error}`)
          eventSource.close()
          state.isStreaming = false
        }
      }

      eventSource.onerror = (err) => {
        console.error('EventSource failed:', err)
        
        // EventSource.readyState:
        // 0: CONNECTING - it is attempting to reconnect
        // 2: CLOSED - it has given up or was closed
        if (eventSource.readyState === EventSource.CONNECTING) {
          state.status = 'reconnecting'
          state.isConnected = false
          state.logs.push('Connection lost. Reconnecting...')
        } else {
          state.error = 'Connection failed'
          state.status = 'error'
          eventSource.close()
          state.isStreaming = false
        }
      }

    } catch (err: any) {
      state.error = err.message
      state.status = 'error'
      state.isStreaming = false
    }
  }

  return { state, runTool, reset }
}
