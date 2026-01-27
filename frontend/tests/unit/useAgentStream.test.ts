import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAgentStream } from '../../src/composables/useAgentStream'

let lastEventSource: MockEventSource | null = null
let lastWebSocket: MockWebSocket | null = null
let wsInstanceCount = 0

class MockEventSource {
  onopen: ((ev: any) => any) | null = null
  onmessage: ((ev: any) => any) | null = null
  onerror: ((ev: any) => any) | null = null
  readyState = 0
  url: string

  constructor(url: string) {
    this.url = url
    lastEventSource = this
    setTimeout(() => {
      if (this.onopen) this.onopen({} as any)
    }, 0)
  }

  close = vi.fn()

  triggerMessage(data: any) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) } as any)
    }
  }

  triggerError(readyState = 2) {
    this.readyState = readyState
    if (this.onerror) {
      this.onerror({} as any)
    }
  }
}

class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  onopen: ((ev: any) => any) | null = null
  onmessage: ((ev: any) => any) | null = null
  onerror: ((ev: any) => any) | null = null
  onclose: ((ev: any) => any) | null = null
  url: string
  readyState = 1 // OPEN

  constructor(url: string) {
    this.url = url
    lastWebSocket = this
    wsInstanceCount++
    setTimeout(() => {
      if (this.onopen) this.onopen({} as any)
    }, 0)
  }

  send = vi.fn()
  close = vi.fn(() => {
    this.readyState = 3 // CLOSED
    if (this.onclose) {
      this.onclose({} as any)
    }
  })

  triggerMessage(data: any) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) } as any)
    }
  }

  triggerError() {
    if (this.onerror) {
      this.onerror({} as any)
    }
  }

  triggerClose() {
    this.readyState = 3 // CLOSED
    if (this.onclose) {
      this.onclose({} as any)
    }
  }
}

global.EventSource = MockEventSource as any
global.WebSocket = MockWebSocket as any

describe('useAgentStream', () => {
  beforeEach(() => {
    lastEventSource = null
    lastWebSocket = null
    wsInstanceCount = 0
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ call_id: 'test-call-id' }),
      })
    ))
  })

  it('initializes with default state', () => {
    const { state } = useAgentStream()
    expect(state.status).toBe('idle')
    expect(state.isConnected).toBe(false)
    expect(state.isStreaming).toBe(false)
  })

  describe('SSE path', () => {
    it('starts streaming and connects to EventSource', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = false
      
      runTool('test_tool', { arg1: 'val1' })
      
      expect(state.status).toBe('connecting')
      expect(state.isStreaming).toBe(true)

      await vi.waitFor(() => expect(state.status).toBe('connected'))
      
      expect(state.callId).toBe('test-call-id')
      expect(state.isConnected).toBe(true)
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/start_task/test_tool',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ args: { arg1: "val1" } })
        })
      )
    })

    it('updates progress on message', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = false
      
      runTool('test_tool')
      
      await vi.waitFor(() => expect(state.status).toBe('connected'))
      
      lastEventSource?.triggerMessage({
        call_id: 'test-call-id',
        type: 'progress',
        payload: { step: 'Working', pct: 50, log: 'Halfway there' }
      })

      expect(state.currentStep).toBe('Working')
      expect(state.progressPct).toBe(50)
      expect(state.logs).toContain('Halfway there')
    })

    it('provides input via REST fallback', async () => {
      const { state, runTool, sendInput } = useAgentStream()
      state.useWS = false
      
      runTool('test_tool')
      await vi.waitFor(() => expect(state.status).toBe('connected'))
      
      lastEventSource?.triggerMessage({
        call_id: 'test-call-id',
        type: 'input_request',
        payload: { prompt: 'Continue?' }
      })

      expect(state.status).toBe('waiting_for_input')
      expect(state.inputPrompt).toBe('Continue?')

      await sendInput('yes')

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/provide_input',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ call_id: 'test-call-id', value: 'yes' })
        })
      )
      expect(state.status).toBe('connected')
    })
  })

  describe('WebSocket path', () => {
    it('starts streaming and connects to WebSocket', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = true
      
      runTool('test_tool', { arg1: 'val1' })
      
      expect(state.status).toBe('connecting')
      expect(state.isStreaming).toBe(true)

      await vi.waitFor(() => expect(state.status).toBe('connected'))
      
      expect(state.isConnected).toBe(true)
      expect(lastWebSocket).not.toBeNull()
      expect(lastWebSocket?.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'start',
        tool_name: 'test_tool',
        args: { arg1: 'val1' }
      }))
    })

    it('captures call_id from WS message', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = true
      
      runTool('test_tool')
      await vi.waitFor(() => expect(state.status).toBe('connected'))
      
      lastWebSocket?.triggerMessage({
        call_id: 'ws-call-id',
        type: 'progress',
        payload: { step: 'Started', pct: 0 }
      })

      expect(state.callId).toBe('ws-call-id')
    })

    it('stops tool via WS', async () => {
      const { state, runTool, stopTool } = useAgentStream()
      state.useWS = true
      
      runTool('test_tool')
      await vi.waitFor(() => expect(state.status).toBe('connected'))
      
      state.callId = 'ws-call-id'
      await stopTool()

      expect(lastWebSocket?.send).toHaveBeenCalledWith(JSON.stringify({
        type: 'stop',
        call_id: 'ws-call-id'
      }))
      expect(state.status).toBe('cancelled')
      expect(state.isStreaming).toBe(false)
    })

    it('handles interactive input via WS', async () => {
        const { state, runTool, sendInput } = useAgentStream()
        state.useWS = true
        
        runTool('test_tool')
        await vi.waitFor(() => expect(state.status).toBe('connected'))
        
        lastWebSocket?.triggerMessage({
          call_id: 'ws-call-id',
          type: 'input_request',
          payload: { prompt: 'Approval?' }
        })
  
        expect(state.status).toBe('waiting_for_input')
        expect(state.inputPrompt).toBe('Approval?')
  
        await sendInput('confirmed')
  
        expect(lastWebSocket?.send).toHaveBeenCalledWith(JSON.stringify({
          type: 'input',
          call_id: 'ws-call-id',
          value: 'confirmed'
        }))
        expect(state.status).toBe('connected')
    })

    it('handles WS completion', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = true
      
      runTool('test_tool')
      await vi.waitFor(() => expect(state.status).toBe('connected'))
      
      lastWebSocket?.triggerMessage({
        call_id: 'test-call-id', // Initially null, will capture this
        type: 'result',
        payload: { success: true }
      })

      expect(state.status).toBe('completed')
      expect(state.result).toEqual({ success: true })
      expect(state.isStreaming).toBe(false)
    })

    it('reuses existing WebSocket connection', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = true
      
      // Run first tool
      runTool('tool_1')
      await vi.waitFor(() => expect(state.status).toBe('connected'))
      expect(wsInstanceCount).toBe(1)
      
      // Complete first tool
      lastWebSocket?.triggerMessage({ call_id: 'tool_1_id', type: 'result', payload: {} })
      expect(state.status).toBe('completed')
      
      // Run second tool
      runTool('tool_2')
      await vi.waitFor(() => expect(state.status).toBe('connected'))
      
      // Should still be only 1 WS instance
      expect(wsInstanceCount).toBe(1)
      expect(lastWebSocket?.send).toHaveBeenCalledWith(expect.stringContaining('tool_2'))
    })

    it('handles unexpected WS closure during streaming', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = true
      
      runTool('test_tool')
      await vi.waitFor(() => expect(state.status).toBe('connected'))
      
      lastWebSocket?.triggerClose()
      
      expect(state.status).toBe('error')
      expect(state.error).toContain('closed unexpectedly')
      expect(state.isStreaming).toBe(false)
      expect(state.isConnected).toBe(false)
    })
  })
})