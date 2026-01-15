import { ref, reactive } from 'vue'

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

export interface AgentState {
  isConnected: boolean
  callId: string | null
  currentStep: string
  progressPct: number
  logs: string[]
  result: any | null
  error: string | null
  isStreaming: boolean
}

export function useAgentStream() {
  const state = reactive<AgentState>({
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

    try {
      // 1. Start Task
      const response = await fetch(`http://localhost:8000/start_task/${toolName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(args)
      })

      if (!response.ok) throw new Error(`Failed to start task: ${response.statusText}`)
      
      const { call_id } = await response.json()
      state.callId = call_id

      // 2. Connect to SSE
      const eventSource = new EventSource(`http://localhost:8000/stream/${call_id}`)

      eventSource.onopen = () => {
        state.isConnected = true
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
          state.logs.push('Task completed successfully.')
          eventSource.close()
          state.isStreaming = false
        } else if (data.type === 'error') {
          state.error = data.payload.detail || 'Unknown error'
          state.logs.push(`Error: ${state.error}`)
          eventSource.close()
          state.isStreaming = false
        }
      }

      eventSource.onerror = (err) => {
        console.error('EventSource failed:', err)
        state.error = 'Connection lost'
        eventSource.close()
        state.isStreaming = false
      }

    } catch (err: any) {
      state.error = err.message
      state.isStreaming = false
    }
  }

  return { state, runTool, reset }
}
