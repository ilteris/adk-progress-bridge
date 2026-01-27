import { reactive, onUnmounted } from 'vue'

interface ProgressPayload {
  step: string
  pct: number
  log?: string
  metadata?: Record<string, any>
}

interface AgentEvent {
  call_id: string
  type: 'progress' | 'result' | 'error' | 'input_request'
  payload: any
}

export type ConnectionStatus = 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'error' | 'completed' | 'cancelled' | 'waiting_for_input'

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
  inputPrompt: string | null
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
    useWS: false,
    inputPrompt: null
  })

  let ws: WebSocket | null = null
  let eventSource: EventSource | null = null

  const reset = (closeWS = true) => {
    state.status = 'idle'
    state.isConnected = false
    state.callId = null
    state.currentStep = 'Idle'
    state.progressPct = 0
    state.logs = []
    state.result = null
    state.error = null
    state.isStreaming = false
    state.inputPrompt = null
    
    if (closeWS && ws) {
      ws.close()
      ws = null
    }
    
    if (eventSource) {
      eventSource.close()
      eventSource = null
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
        body: JSON.stringify({
            args: args
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to start task: ${response.statusText}`)
      }
      
      const { call_id } = await response.json()
      state.callId = call_id

      // 2. Connect to SSE
      const streamUrl = new URL(`${API_BASE_URL}/stream`)
      streamUrl.searchParams.append('call_id', call_id)
      if (BRIDGE_API_KEY) {
        streamUrl.searchParams.append('api_key', BRIDGE_API_KEY)
      }

      eventSource = new EventSource(streamUrl.toString())

      eventSource.onopen = () => {
        state.isConnected = true
        state.status = 'connected'
        state.error = null
        state.logs.push('Connected to SSE stream...')
      }

      eventSource.onmessage = (event) => {
        const data: AgentEvent = JSON.parse(event.data)
        // Ensure we only process events for the current call_id
        if (data.call_id === state.callId) {
            handleEvent(data, () => eventSource?.close())
        }
      }

      eventSource.onerror = (err) => {
        console.error('EventSource failed:', err)
        if (eventSource?.readyState === EventSource.CONNECTING) {
          state.status = 'reconnecting'
          state.isConnected = false
          state.logs.push('Connection lost. Reconnecting SSE...')
        } else {
          state.error = 'Connection failed'
          state.status = 'error'
          eventSource?.close()
          state.isStreaming = false
        }
      }
    } catch (err: any) {
      state.error = err.message
      state.status = 'error'
      state.isStreaming = false
    }
  }

  const connectWS = (): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      const wsUrl = new URL(`${WS_BASE_URL}/ws`)
      if (BRIDGE_API_KEY) {
        wsUrl.searchParams.append('api_key', BRIDGE_API_KEY)
      }

      ws = new WebSocket(wsUrl.toString())

      ws.onopen = () => {
        state.isConnected = true
        state.logs.push('Connected to WebSocket...')
        resolve()
      }

      ws.onmessage = (event) => {
        const data: AgentEvent = JSON.parse(event.data)
        
        // If we don't have a callId yet, this might be the start of our new task
        if (!state.callId && data.call_id) {
            state.callId = data.call_id
        }
        
        // Only handle events matching our current callId to avoid ghost tasks
        if (data.call_id === state.callId) {
            handleEvent(data, () => {
                state.isStreaming = false
            })
        }
      }

      ws.onerror = (err) => {
        console.error('WebSocket error:', err)
        state.error = 'WebSocket connection failed'
        state.status = 'error'
        state.isStreaming = false
        reject(err)
      }

      ws.onclose = () => {
        state.isConnected = false
        if (state.isStreaming) {
          state.error = 'WebSocket connection closed unexpectedly'
          state.status = 'error'
          state.isStreaming = false
          state.logs.push('Error: WebSocket closed unexpectedly during streaming.')
        } else if (state.status !== 'completed' && state.status !== 'error' && state.status !== 'cancelled') {
          state.status = 'idle'
        }
        state.logs.push('WebSocket closed.')
        ws = null
      }
    })
  }

  const runToolWS = async (toolName: string, args: Record<string, any>) => {
    try {
      await connectWS()
      state.status = 'connected'
      
      ws?.send(JSON.stringify({
        type: 'start',
        tool_name: toolName,
        args: args
      }))
    } catch (err) {
      // Error handled in connectWS
    }
  }

  const stopTool = async () => {
    if (state.useWS && ws && state.callId && state.isStreaming) {
      ws.send(JSON.stringify({
        type: 'stop',
        call_id: state.callId
      }))
      state.status = 'cancelled'
      state.isStreaming = false
    } else if (state.callId && state.isStreaming) {
      try {
        const headers: Record<string, string> = {}
        if (BRIDGE_API_KEY) {
          headers['X-API-Key'] = BRIDGE_API_KEY
        }
        await fetch(`${API_BASE_URL}/stop_task/${state.callId}`, {
          method: 'POST',
          headers
        })
      } catch (err) {
        console.error('Failed to stop SSE task on backend:', err)
      }
      
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
      
      state.status = 'cancelled'
      state.logs.push('Task stopped by user.')
      state.isStreaming = false
    } else {
      reset()
    }
  }

  const sendInput = async (value: string) => {
    if (state.callId && state.status === 'waiting_for_input') {
        if (state.useWS && ws) {
            ws.send(JSON.stringify({
                type: 'input',
                call_id: state.callId,
                value: value
            }))
        } else {
            try {
                const headers: Record<string, string> = { 'Content-Type': 'application/json' }
                if (BRIDGE_API_KEY) {
                    headers['X-API-Key'] = BRIDGE_API_KEY
                }
                await fetch(`${API_BASE_URL}/provide_input`, {
                    method: 'POST',
                    headers,
                    body: JSON.stringify({
                        call_id: state.callId,
                        value: value
                    })
                })
            } catch (err) {
                console.error('Failed to send input via POST:', err)
            }
        }
        state.status = 'connected'
        state.inputPrompt = null
        state.logs.push(`Sent input: ${value}`)
    }
  }

  const handleEvent = (data: AgentEvent, closeFn: () => void) => {
    if (data.type === 'progress') {
      const payload = data.payload as ProgressPayload
      state.currentStep = payload.step
      state.progressPct = payload.pct
      if (payload.log) state.logs.push(payload.log)
    } else if (data.type === 'input_request') {
        state.status = 'waiting_for_input'
        state.inputPrompt = data.payload.prompt
        state.logs.push(`AGENT REQUESTED INPUT: ${state.inputPrompt}`)
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
    // 1. If already streaming, stop it first
    if (state.isStreaming) {
      await stopTool()
    }

    const useWS = state.useWS
    // 2. Reset state (but keep WS open if using WS)
    reset(!useWS)
    state.useWS = useWS 
    state.isStreaming = true
    state.status = 'connecting'

    if (state.useWS) {
      await runToolWS(toolName, args)
    } else {
      await runToolSSE(toolName, args)
    }
  }

  onUnmounted(() => {
    if (ws) ws.close()
    if (eventSource) eventSource.close()
  })
  
  return { state, runTool, stopTool, sendInput, reset }
}