import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAgentStream, wsManager } from '../../src/composables/useAgentStream'

let lastWebSocket: MockWebSocket | null = null
let wsInstanceCount = 0

class MockWebSocket extends EventTarget {
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
    super()
    this.url = url
    lastWebSocket = this
    wsInstanceCount++
    // Use a slightly longer timeout to ensure the listener can be attached
    setTimeout(() => {
      if (this.onopen) this.onopen({} as any)
    }, 10)
  }

  send = vi.fn()
  close = vi.fn(() => {
    this.readyState = 3 // CLOSED
    if (this.onclose) {
      this.onclose({} as any)
    }
    const event = new Event('close')
    this.dispatchEvent(event)
  })

  triggerMessage(data: any) {
    const event = new MessageEvent('message', { data: JSON.stringify(data) })
    this.dispatchEvent(event)
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
    const event = new Event('close')
    this.dispatchEvent(event)
  }
}

global.WebSocket = MockWebSocket as any

describe('useAgentStream', () => {
  beforeEach(() => {
    lastWebSocket = null
    wsInstanceCount = 0
    wsManager.reset()
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

  describe('WebSocket path', () => {
    it('starts streaming and connects to WebSocket', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = true
      
      const runPromise = runTool('test_tool', { arg1: 'val1' })
      
      // Wait for WS to be created and connected
      await vi.waitFor(() => expect(lastWebSocket).not.toBeNull())
      
      // Give it a moment to resolve the connect() promise and enter startTask
      await new Promise(r => setTimeout(r, 50))

      lastWebSocket?.triggerMessage({
        call_id: 'ws-call-id',
        type: 'progress',
        payload: { step: 'Started', pct: 0 }
      })

      await runPromise

      expect(state.isConnected).toBe(true)
      expect(state.status).toBe('connected')
      expect(state.callId).toBe('ws-call-id')
    })

    it('reuses existing WebSocket connection', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = true
      
      // Run first tool
      const run1 = runTool('tool_1')
      await vi.waitFor(() => expect(lastWebSocket).not.toBeNull())
      await new Promise(r => setTimeout(r, 50))
      
      lastWebSocket?.triggerMessage({ call_id: 'tool_1_id', type: 'progress', payload: { step: 'Started', pct: 0 } })
      await run1
      
      expect(wsInstanceCount).toBe(1)
      
      // Complete first tool
      lastWebSocket?.triggerMessage({ call_id: 'tool_1_id', type: 'result', payload: {} })
      expect(state.status).toBe('completed')
      
      // Run second tool
      const run2 = runTool('tool_2')
      await new Promise(r => setTimeout(r, 50))
      lastWebSocket?.triggerMessage({ call_id: 'tool_2_id', type: 'progress', payload: { step: 'Started', pct: 0 } })
      await run2
      
      expect(wsInstanceCount).toBe(1)
    })

    it('handles unexpected WS closure during streaming', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = true
      
      const runPromise = runTool('test_tool')
      await vi.waitFor(() => expect(lastWebSocket).not.toBeNull())
      await new Promise(r => setTimeout(r, 50))
      
      lastWebSocket?.triggerMessage({ call_id: 'ws-call-id', type: 'progress', payload: { step: 'Started', pct: 0 } })
      await runPromise
      
      lastWebSocket?.triggerClose()
      
      expect(state.status).toBe('error')
      expect(state.error).toContain('WebSocket connection closed')
    })
  })
})