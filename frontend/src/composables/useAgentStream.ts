import { reactive, onUnmounted, getCurrentInstance } from 'vue'

interface ProgressPayload {
  step: string
  pct: number
  log?: string
  metadata?: Record<string, any>
}

interface AgentEvent {
  call_id: string
  type: 'progress' | 'result' | 'error' | 'input_request' | 'task_started' | 'reconnecting' | 'stop_success' | 'input_success' | 'tools_list'
  payload: any
  request_id?: string
  tools?: string[]
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
  tools: string[]
}

// Support VITE_API_URL environment variable, defaulting to localhost for dev
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS_BASE_URL = API_BASE_URL.replace('http', 'ws')
// Support VITE_BRIDGE_API_KEY for authenticated requests
const BRIDGE_API_KEY = import.meta.env.VITE_BRIDGE_API_KEY || ''

// Configuration Constants for WebSocket behavior (Configurable via Environment Variables)
// WS_HEARTBEAT_INTERVAL: Frequency (ms) to send a ping to the server to keep connection alive.
const WS_HEARTBEAT_INTERVAL = Number(import.meta.env.VITE_WS_HEARTBEAT_INTERVAL) || 30000
// WS_RECONNECT_MAX_ATTEMPTS: Maximum number of times to try reconnecting before giving up.
const WS_RECONNECT_MAX_ATTEMPTS = Number(import.meta.env.VITE_WS_RECONNECT_MAX_ATTEMPTS) || 10
// WS_REQUEST_TIMEOUT: Max time (ms) to wait for a response to start/list_tools commands.
const WS_REQUEST_TIMEOUT = Number(import.meta.env.VITE_WS_REQUEST_TIMEOUT) || 5000
// WS_RECONNECT_INITIAL_DELAY: Initial delay (ms) for exponential backoff during reconnection.
const WS_RECONNECT_INITIAL_DELAY = Number(import.meta.env.VITE_WS_RECONNECT_INITIAL_DELAY) || 1000
// WS_RECONNECT_MAX_DELAY: Maximum delay (ms) between reconnection attempts.
const WS_RECONNECT_MAX_DELAY = Number(import.meta.env.VITE_WS_RECONNECT_MAX_DELAY) || 30000
// WS_BUFFER_SIZE: Number of messages to buffer if they arrive before a subscriber is ready.
const WS_BUFFER_SIZE = Number(import.meta.env.VITE_WS_BUFFER_SIZE) || 1000

/**
 * Shared WebSocket Manager to support multiple concurrent tasks over a single connection.
 * Enhanced with automatic reconnection and heartbeat support.
 */
export class WebSocketManager {
  private ws: WebSocket | null = null
  private subscribers: Map<string, (event: AgentEvent) => void> = new Map()
  private requestCallbacks: Map<string, { resolve: (data: any) => void, reject: (err: any) => void, timeout: any }> = new Map()
  private messageBuffer: AgentEvent[] = []
  private connectionPromise: Promise<void> | null = null
  private heartbeatInterval: any = null
  private reconnectTimeout: any = null
  private reconnectAttempts: number = 0
  private maxReconnectAttempts: number = WS_RECONNECT_MAX_ATTEMPTS
  private isManuallyClosed: boolean = false

  // For testing
  public reset() {
    this.isManuallyClosed = true
    this.stopHeartbeat()
    this.clearReconnect()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.subscribers.clear()
    this.messageBuffer = []
    for (const req of this.requestCallbacks.values()) {
        clearTimeout(req.timeout)
        req.reject(new Error('WebSocket manager reset'))
    }
    this.requestCallbacks.clear()
    this.connectionPromise = null
    this.reconnectAttempts = 0
  }

  async connect(): Promise<void> {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
        if (this.connectionPromise) return this.connectionPromise
        return Promise.resolve()
    }
    
    if (this.connectionPromise) return this.connectionPromise

    this.isManuallyClosed = false
    this.connectionPromise = new Promise((resolve, reject) => {
      const wsUrl = new URL(`${WS_BASE_URL}/ws`)
      if (BRIDGE_API_KEY) {
        wsUrl.searchParams.append('api_key', BRIDGE_API_KEY)
      }

      console.log(`[WS] Connecting to ${wsUrl.toString()}...`)
      this.ws = new WebSocket(wsUrl.toString())

      this.ws.onopen = () => {
        console.log('[WS] Connection established')
        this.startHeartbeat()
        this.reconnectAttempts = 0
        this.connectionPromise = null
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
            const data: any = JSON.parse(event.data)
            // Handle pong for heartbeat
            if (data.type === 'pong') return

            // Handle request_id correlations
            if (data.request_id && this.requestCallbacks.has(data.request_id)) {
                const { resolve: reqResolve, reject: reqReject, timeout } = this.requestCallbacks.get(data.request_id)!
                clearTimeout(timeout)
                this.requestCallbacks.delete(data.request_id)
                
                if (data.type === 'error') {
                    reqReject(new Error(data.payload?.detail || 'Request failed'))
                } else {
                    reqResolve(data)
                }
                return
            }

            // Handle task-specific events
            const callback = this.subscribers.get(data.call_id)
            if (callback) {
                callback(data)
            } else if (data.call_id) {
                // Buffer message if no subscriber yet
                this.messageBuffer.push(data)
                if (this.messageBuffer.length > WS_BUFFER_SIZE) {
                    this.messageBuffer.shift()
                }
            }
        } catch (e) {
            console.error('[WS] Failed to parse message', e)
        }
      }

      this.ws.onerror = (err) => {
        console.error('[WS] Connection error', err)
        this.connectionPromise = null
        reject(err)
      }

      this.ws.onclose = (event) => {
        console.warn(`[WS] Connection closed: ${event.code} ${event.reason}`)
        this.stopHeartbeat()
        this.ws = null
        this.connectionPromise = null

        if (!this.isManuallyClosed) {
            this.notifyStatusToAll('reconnecting')
            this.scheduleReconnect()
        } else {
            // Error out all active subscribers if manually closed or failed permanently
            this.notifyErrorToAll('WebSocket connection closed')
            this.subscribers.clear()
            this.messageBuffer = []
            
            // Reject all pending requests
            for (const [reqId, req] of this.requestCallbacks.entries()) {
                clearTimeout(req.timeout)
                req.reject(new Error('WebSocket connection closed'))
                this.requestCallbacks.delete(reqId)
            }
        }
      }
    })

    return this.connectionPromise
  }

  private notifyStatusToAll(type: 'reconnecting') {
    for (const [callId, callback] of this.subscribers.entries()) {
        callback({
            call_id: callId,
            type: type,
            payload: {}
        })
    }
  }

  private notifyErrorToAll(detail: string) {
    for (const [callId, callback] of this.subscribers.entries()) {
        callback({
            call_id: callId,
            type: 'error',
            payload: { detail }
        })
    }
  }

  private scheduleReconnect() {
    this.clearReconnect()
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('[WS] Max reconnect attempts reached')
        this.notifyErrorToAll('WebSocket connection failed permanently')
        this.subscribers.clear()
        this.messageBuffer = []
        return
    }

    const delay = Math.min(WS_RECONNECT_INITIAL_DELAY * Math.pow(2, this.reconnectAttempts), WS_RECONNECT_MAX_DELAY)
    console.log(`[WS] Scheduling reconnect in ${delay}ms (Attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`)
    
    this.reconnectTimeout = setTimeout(() => {
        this.reconnectAttempts++
        this.connect().catch(err => {
            console.error('[WS] Reconnect failed', err)
            // onclose will be triggered again if connection fails during handshake
        })
    }, delay)
  }

  private clearReconnect() {
    if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout)
        this.reconnectTimeout = null
    }
  }

  private startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, WS_HEARTBEAT_INTERVAL)
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  subscribe(callId: string, callback: (event: AgentEvent) => void) {
    this.subscribers.set(callId, callback)
    
    // Replay and clear buffered messages for this callId
    const relevantMessages = this.messageBuffer.filter(msg => msg.call_id === callId)
    if (relevantMessages.length > 0) {
        console.log(`[WS] Replaying ${relevantMessages.length} buffered messages for ${callId}`)
        relevantMessages.forEach(msg => callback(msg))
        this.messageBuffer = this.messageBuffer.filter(msg => msg.call_id !== callId)
    }
  }

  unsubscribe(callId: string) {
    this.subscribers.delete(callId)
    // Also clear any remaining buffered messages for this callId to prevent leaks
    this.messageBuffer = this.messageBuffer.filter(msg => msg.call_id !== callId)
  }

  send(data: any): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
      return true
    } else {
        console.warn('[WS] Cannot send message, WebSocket not open')
        return false
    }
  }

  /**
   * Sends a message over WebSocket and waits for a response with a matching request_id.
   * Enables reliable command-response cycles for high-concurrency environments.
   */
  public async sendWithCorrelation(data: any, timeoutMs: number = WS_REQUEST_TIMEOUT): Promise<any> {
      await this.connect()
      const requestId = Math.random().toString(36).substring(2, 11)
      data.request_id = requestId

      return new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
              this.requestCallbacks.delete(requestId)
              reject(new Error(`Timeout waiting for response to ${data.type}`))
          }, timeoutMs)

          this.requestCallbacks.set(requestId, { resolve, reject, timeout })
          const sent = this.send(data)
          if (!sent) {
              clearTimeout(timeout)
              this.requestCallbacks.delete(requestId)
              reject(new Error(`Failed to send ${data.type}: WebSocket not open`))
          }
      })
  }

  async startTask(toolName: string, args: any, onEvent: (event: AgentEvent) => void): Promise<string> {
    const data = await this.sendWithCorrelation({
        type: 'start',
        tool_name: toolName,
        args: args
    })
    
    this.subscribe(data.call_id, onEvent)
    return data.call_id
  }

  async getTools(): Promise<string[]> {
    const data = await this.sendWithCorrelation({
        type: 'list_tools'
    })
    return data.tools
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
    inputPrompt: null,
    tools: []
  })

  let eventSource: EventSource | null = null

  const reset = () => {
    if (state.useWS && state.callId) {
        wsManager.unsubscribe(state.callId)
    }

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

  const fetchTools = async (): Promise<string[]> => {
    try {
      let tools: string[] = []
      if (state.useWS) {
          tools = await wsManager.getTools()
      } else {
          const headers: Record<string, string> = {}
          if (BRIDGE_API_KEY) {
              headers['X-API-Key'] = BRIDGE_API_KEY
          }
          const response = await fetch(`${API_BASE_URL}/tools`, { headers })
          if (!response.ok) throw new Error('Failed to fetch tools via REST')
          tools = await response.json()
      }
      state.tools = tools
      return tools
    } catch (err: any) {
      console.error('Failed to fetch tools:', err)
      return []
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
      try {
        await wsManager.sendWithCorrelation({
          type: 'stop',
          call_id: state.callId
        })
        state.logs.push('Stop command acknowledged by server.')
        state.status = 'cancelled'
        state.isStreaming = false
      } catch (err: any) {
          state.error = `Failed to send stop command: ${err.message}`
          state.status = 'error'
          state.isStreaming = false
          reset()
      }
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
            try {
                await wsManager.sendWithCorrelation({
                    type: 'input',
                    call_id: state.callId,
                    value: value
                })
                state.logs.push('Input command acknowledged by server.')
                state.logs.push(`Sent input: ${value}`)
            } catch (err: any) {
                state.error = `Failed to send input: ${err.message}`
                state.status = 'error'
                return
            }
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
                state.logs.push(`Sent input: ${value}`)
            } catch (err) {}
        }
        state.status = 'connected'
        state.inputPrompt = null
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
    } else if (data.type === 'reconnecting') {
        state.status = 'reconnecting'
        state.isConnected = false
        state.logs.push('WebSocket connection lost. Reconnecting...')
    } else if (data.type === 'stop_success') {
        state.logs.push('Stop command acknowledged by server.')
        // stop_success is the final acknowledgement for a stop command
        closeFn()
    } else if (data.type === 'input_success') {
        state.logs.push('Input command acknowledged by server.')
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
  
  return { state, runTool, stopTool, sendInput, reset, fetchTools }
}