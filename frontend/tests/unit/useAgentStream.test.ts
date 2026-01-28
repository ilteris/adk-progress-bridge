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

  send = vi.fn((data: string) => {
    const parsed = JSON.parse(data)
    if (parsed.type === 'start') {
        // Automatically respond with task_started
        setTimeout(() => {
            this.triggerMessage({
                type: 'task_started',
                call_id: 'ws-call-id-' + parsed.tool_name,
                request_id: parsed.request_id
            })
        }, 10)
    } else if (parsed.type === 'list_tools') {
        // Automatically respond with tools_list
        setTimeout(() => {
            this.triggerMessage({
                type: 'tools_list',
                tools: ['tool1', 'tool2'],
                request_id: parsed.request_id
            })
        }, 10)
    }
  })

  close = vi.fn(() => {
    this.readyState = 3 // CLOSED
    if (this.onclose) {
      this.onclose({ code: 1000, reason: 'Normal Closure' } as any)
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
      this.onclose({ code: 1006, reason: 'Abnormal Closure' } as any)
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

  it('fetches tools via REST when useWS is false', async () => {
    const { fetchTools } = useAgentStream()
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(['rest_tool1', 'rest_tool2']),
      })
    ))
    
    const tools = await fetchTools()
    expect(tools).toEqual(['rest_tool1', 'rest_tool2'])
    expect(global.fetch).toHaveBeenCalled()
  })

  it('fetches tools via WS when useWS is true', async () => {
    const { state, fetchTools } = useAgentStream()
    state.useWS = true
    
    const toolsPromise = fetchTools()
    
    // Wait for WS to be created
    await vi.waitFor(() => expect(lastWebSocket).not.toBeNull())
    
    const tools = await toolsPromise
    expect(tools).toEqual(['tool1', 'tool2'])
    expect(lastWebSocket?.send).toHaveBeenCalledWith(expect.stringContaining('"type":"list_tools"'))
  })

  describe('WebSocket path', () => {
    it('starts streaming and connects to WebSocket', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = true
      
      const runPromise = runTool('test_tool', { arg1: 'val1' })
      
      // Wait for WS to be created and connected
      await vi.waitFor(() => expect(lastWebSocket).not.toBeNull())
      
      // Give it a moment to resolve the connect() promise and enter startTask
      await new Promise(r => setTimeout(r, 100))

      lastWebSocket?.triggerMessage({
        call_id: 'ws-call-id-test_tool',
        type: 'progress',
        payload: { step: 'Started', pct: 0 }
      })

      lastWebSocket?.triggerMessage({
        call_id: 'ws-call-id-test_tool',
        type: 'result',
        payload: { ok: true }
      })

      await runPromise

      expect(state.isConnected).toBe(true)
      expect(state.status).toBe('completed')
      expect(state.callId).toBe('ws-call-id-test_tool')
    })

    it('reuses existing WebSocket connection', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = true
      
      // Run first tool
      const run1 = runTool('tool_1')
      await vi.waitFor(() => expect(lastWebSocket).not.toBeNull())
      await new Promise(r => setTimeout(r, 100))
      
      lastWebSocket?.triggerMessage({ call_id: 'ws-call-id-tool_1', type: 'progress', payload: { step: 'Started', pct: 0 } })
      lastWebSocket?.triggerMessage({ call_id: 'ws-call-id-tool_1', type: 'result', payload: {} })
      await run1
      
      expect(wsInstanceCount).toBe(1)
      expect(state.status).toBe('completed')
      
      // Run second tool
      const run2 = runTool('tool_2')
      await new Promise(r => setTimeout(r, 100))
      lastWebSocket?.triggerMessage({ call_id: 'ws-call-id-tool_2', type: 'progress', payload: { step: 'Started', pct: 0 } })
      lastWebSocket?.triggerMessage({ call_id: 'ws-call-id-tool_2', type: 'result', payload: {} })
      await run2
      
      expect(wsInstanceCount).toBe(1)
      expect(state.status).toBe('completed')
    })

    it('handles unexpected WS closure during streaming by reconnecting', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = true
      
      const runPromise = runTool('test_tool')
      await vi.waitFor(() => expect(lastWebSocket).not.toBeNull())
      await new Promise(r => setTimeout(r, 100))
      
      lastWebSocket?.triggerMessage({ call_id: 'ws-call-id-test_tool', type: 'progress', payload: { step: 'Started', pct: 0 } })
      
      lastWebSocket?.triggerClose()
      
      await new Promise(r => setTimeout(r, 50))
      
      expect(state.status).toBe('reconnecting')
      expect(state.isConnected).toBe(false)
      expect(state.logs[state.logs.length - 1]).toContain('Reconnecting')
    })
  })
})
