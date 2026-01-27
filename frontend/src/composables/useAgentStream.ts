import { reactive, onUnmounted } from 'vue'

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
  useWS: boolean
}

// Support VITE_API_URL environment variable, defaulting to localhost for dev
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS_BASE_URL = API_BASE_URL.replace('http', 'ws')
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
    isStreaming: false,
    useWS: false
  })

  let ws: WebSocket | null = null

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
    if (ws) {
      ws.close()
      ws = null
    }
  }

  const runToolSSE = async (toolName: string, args: Record<string, any>) => {
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
      const streamUrl = new URL(`${API_BASE_URL}/stream/${call_id}`)
      if (BRIDGE_API_KEY) {
        streamUrl.searchParams.append('api_key', BRIDGE_API_KEY)
      }

      const eventSource = new EventSource(streamUrl.toString())

      eventSource.onopen = () => {
        state.isConnected = true
        state.status = 'connected'
        state.error = null
        state.logs.push('Connected to SSE stream...')
      }

      eventSource.onmessage = (event) => {
        const data: AgentEvent = JSON.parse(event.data)
        handleEvent(data, () => eventSource.close())
      }

      eventSource.onerror = (err) => {
        console.error('EventSource failed:', err)
        if (eventSource.readyState === EventSource.CONNECTING) {
          state.status = 'reconnecting'
          state.isConnected = false
          state.logs.push('Connection lost. Reconnecting SSE...')
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

  const runToolWS = (toolName: string, args: Record<string, any>) => {
    const wsUrl = new URL(`${WS_BASE_URL}/ws`)
    if (BRIDGE_API_KEY) {
      wsUrl.searchParams.append('api_key', BRIDGE_API_KEY)
    }

    ws = new WebSocket(wsUrl.toString())

    ws.onopen = () => {
      state.isConnected = true
      state.status = 'connected'
      state.logs.push('Connected to WebSocket...')
      
      ws?.send(JSON.stringify({
        type: 'start',
        tool_name: toolName,
        args: args
      }))
    }

    ws.onmessage = (event) => {
      const data: AgentEvent = JSON.parse(event.data)
      handleEvent(data, () => {
          // WS stays open, but we might want to mark as not streaming
          state.isStreaming = false
      })
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
      state.error = 'WebSocket connection failed'
      state.status = 'error'
      state.isStreaming = false
    }

    ws.onclose = () => {
      state.isConnected = false
      if (state.status !== 'completed' && state.status !== 'error') {
          state.status = 'idle'
      }
      state.logs.push('WebSocket closed.')
    }
  }

  const handleEvent = (data: AgentEvent, closeFn: () => void) => {
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
      state.isStreaming = false
      closeFn()
    } else if (data.type === 'error') {
      state.error = data.payload.detail || 'Unknown error'
      state.status = 'error'
      state.logs.push(`Error: ${state.error}`)
      state.isStreaming = false
      closeFn()
    }
  }

  const runTool = async (toolName: string, args: Record<string, any> = {}) => {
    const useWS = state.useWS
    reset()
    state.useWS = useWS // preserve the setting
    state.isStreaming = true
    state.status = 'connecting'

    if (state.useWS) {
      runToolWS(toolName, args)
    } else {
      await runToolSSE(toolName, args)
    }
  }

  onUnmounted(() => {
    if (ws) ws.close()
  })

  return { state, runTool, reset }
}