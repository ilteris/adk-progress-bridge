import { reactive, onUnmounted, getCurrentInstance } from 'vue'

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

/**
 * Shared WebSocket Manager to support multiple concurrent tasks over a single connection.
 */
export class WebSocketManager {
  private ws: WebSocket | null = null
  private subscribers: Map<string, (event: AgentEvent) => void> = new Map()
  private connectionPromise: Promise<void> | null = null
  private heartbeatInterval: any = null

  // For testing
  public reset() {
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.subscribers.clear()
    this.connectionPromise = null
  }

  async connect(): Promise<void> {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
        if (this.connectionPromise) return this.connectionPromise
        return Promise.resolve()
    }
    
    if (this.connectionPromise) return this.connectionPromise

    this.connectionPromise = new Promise((resolve, reject) => {
      const wsUrl = new URL(`${WS_BASE_URL}/ws`)
      if (BRIDGE_API_KEY) {
        wsUrl.searchParams.append('api_key', BRIDGE_API_KEY)
      }

      this.ws = new WebSocket(wsUrl.toString())

      this.ws.onopen = () => {
        this.startHeartbeat()
        this.connectionPromise = null
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
            const data: AgentEvent = JSON.parse(event.data)
            const callback = this.subscribers.get(data.call_id)
            if (callback) {
                callback(data)
            }
        } catch (e) {
            console.error('[WS] Failed to parse message', e)
        }
      }

      this.ws.onerror = (err) => {
        this.connectionPromise = null
        reject(err)
      }

      this.ws.onclose = () => {
        this.stopHeartbeat()
        this.ws = null
        this.connectionPromise = null
        // Error out all active subscribers
        for (const [callId, callback] of this.subscribers.entries()) {
            callback({
                call_id: callId,
                type: 'error',
                payload: { detail: 'WebSocket connection closed' }
            })
        }
        this.subscribers.clear()
      }
    })

    return this.connectionPromise
  }

  private startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  subscribe(callId: string, callback: (event: AgentEvent) => void) {
    this.subscribers.set(callId, callback)
  }

  unsubscribe(callId: string) {
    this.subscribers.delete(callId)
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  async startTask(toolName: string, args: any, onEvent: (event: AgentEvent) => void): Promise<string> {
    await this.connect()
    
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            this.ws?.removeEventListener('message', tempListener)
            reject(new Error('Timeout waiting for task start'))
        }, 5000)

        const tempListener = (event: MessageEvent) => {
            try {
                const data = JSON.parse(event.data)
                if (data.call_id && data.type !== 'ping') {
                    clearTimeout(timeout)
                    this.ws?.removeEventListener('message', tempListener)
                    this.subscribe(data.call_id, onEvent)
                    onEvent(data)
                    resolve(data.call_id)
                }
            } catch (e) {}
        }
        
        this.ws?.addEventListener('message', tempListener)
        
        this.send({
            type: 'start',
            tool_name: toolName,
            args: args
        })
    })
  }
}

export const wsManager = new WebSocketManager()

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

  let eventSource: EventSource | null = null

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
    state.inputPrompt = null
    
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  const runToolSSE = async (toolName: string, args: Record<string, any>) => {
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (BRIDGE_API_KEY) {
        headers['X-API-Key'] = BRIDGE_API_KEY
      }

      const response = await fetch(`${API_BASE_URL}/start_task/${toolName}`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ args })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to start task: ${response.statusText}`)
      }
      
      const { call_id } = await response.json()
      state.callId = call_id

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
        if (data.call_id === state.callId) {
            handleEvent(data, () => eventSource?.close())
        }
      }

      eventSource.onerror = (err) => {
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

  const runToolWS = async (toolName: string, args: Record<string, any>) => {
    try {
      state.status = 'connecting'
      const callId = await wsManager.startTask(toolName, args, (event) => {
        handleEvent(event, () => {
            wsManager.unsubscribe(callId)
        })
      })
      state.callId = callId
      state.isConnected = true
      state.status = 'connected'
    } catch (err: any) {
      state.error = err.message || 'WebSocket error'
      state.status = 'error'
      state.isStreaming = false
    }
  }

  const stopTool = async () => {
    if (state.useWS && state.callId && state.isStreaming) {
      wsManager.send({
        type: 'stop',
        call_id: state.callId
      })
      state.status = 'cancelled'
      state.isStreaming = false
      wsManager.unsubscribe(state.callId)
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
      } catch (err) {}
      
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
        if (state.useWS) {
            wsManager.send({
                type: 'input',
                call_id: state.callId,
                value: value
            })
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
            } catch (err) {}
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
    if (state.isStreaming) {
      await stopTool()
    }

    const useWS = state.useWS
    reset()
    state.useWS = useWS 
    state.isStreaming = true

    if (state.useWS) {
      await runToolWS(toolName, args)
    } else {
      await runToolSSE(toolName, args)
    }
  }

  if (getCurrentInstance()) {
    onUnmounted(() => {
      if (state.isStreaming) {
          stopTool()
      }
      if (eventSource) eventSource.close()
    })
  }
  
  return { state, runTool, stopTool, sendInput, reset }
}