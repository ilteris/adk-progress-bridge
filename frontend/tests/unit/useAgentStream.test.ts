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
      const event = new Event('open')
      this.dispatchEvent(event)
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
    } else if (parsed.type === 'stop') {
        // Automatically respond with stop_success
        setTimeout(() => {
            this.triggerMessage({
                type: 'stop_success',
                call_id: parsed.call_id,
                request_id: parsed.request_id,
                payload: {}
            })
        }, 10)
    } else if (parsed.type === 'input') {
        // Automatically respond with input_success
        setTimeout(() => {
            this.triggerMessage({
                type: 'input_success',
                call_id: parsed.call_id,
                request_id: parsed.request_id,
                payload: {}
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
      
      runTool('test_tool', { arg1: 'val1' })
      
      // Wait for WS to be created and connected
      await vi.waitFor(() => expect(state.status).toBe('connected'))

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

      expect(state.isConnected).toBe(true)
      expect(state.status).toBe('completed')
      expect(state.callId).toBe('ws-call-id-test_tool')
    })

    it('reuses existing WebSocket connection', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = true
      
      // Run first tool
      runTool('tool_1')
      await vi.waitFor(() => expect(state.status).toBe('connected'))
      lastWebSocket?.triggerMessage({ call_id: 'ws-call-id-tool_1', type: 'result', payload: {} })
      await vi.waitFor(() => expect(state.status).toBe('completed'))
      
      expect(wsInstanceCount).toBe(1)
      
      // Run second tool
      runTool('tool_2')
      await vi.waitFor(() => expect(state.status).toBe('connected'))
      lastWebSocket?.triggerMessage({ call_id: 'ws-call-id-tool_2', type: 'result', payload: {} })
      await vi.waitFor(() => expect(state.status).toBe('completed'))
      
      expect(wsInstanceCount).toBe(1)
    })

    it('handles unexpected WS closure during streaming by reconnecting', async () => {
      const { state, runTool } = useAgentStream()
      state.useWS = true
      
      runTool('test_tool')
      await vi.waitFor(() => expect(state.status).toBe('connected'))
      
      lastWebSocket?.triggerMessage({ call_id: 'ws-call-id-test_tool', type: 'progress', payload: { step: 'Started', pct: 0 } })
      
      lastWebSocket?.triggerClose()
      
      await vi.waitFor(() => expect(state.status).toBe('reconnecting'))
      expect(state.isConnected).toBe(false)
      expect(state.logs[state.logs.length - 1]).toContain('Reconnecting')
    })

    it('handles stopTool by sending stop message and waiting for stop_success', async () => {
      const { state, runTool, stopTool } = useAgentStream()
      state.useWS = true
      
      runTool('test_tool')
      await vi.waitFor(() => expect(state.status).toBe('connected'))
      
      // Use a timeout to ensure we don't hang if stopTool fails
      const stopPromise = stopTool()
      
      await stopPromise
      
      expect(state.status).toBe('cancelled')
      expect(state.isStreaming).toBe(false)
      expect(state.logs).toContain('Stop command acknowledged by server.')
    })

    it('reset() cleans up WebSocket subscription', async () => {
        const { state, runTool, reset } = useAgentStream()
        state.useWS = true
        
        runTool('test_tool')
        await vi.waitFor(() => expect(state.status).toBe('connected'))
        
        const unsubscribeSpy = vi.spyOn(wsManager, 'unsubscribe')
        reset()
        
        expect(unsubscribeSpy).toHaveBeenCalledWith('ws-call-id-test_tool')
        expect(state.callId).toBeNull()
    })

    it('replays buffered messages when subscribing late', async () => {
        // Connect WS first
        await wsManager.connect()
        await vi.waitFor(() => expect(lastWebSocket).not.toBeNull())

        // Trigger message BEFORE subscribe
        const callId = 'late-sub-call-id'
        lastWebSocket?.triggerMessage({
            call_id: callId,
            type: 'progress',
            payload: { step: 'Buffered', pct: 50 }
        })

        // Now subscribe
        const callback = vi.fn()
        wsManager.subscribe(callId, callback)

        expect(callback).toHaveBeenCalledWith(expect.objectContaining({
            call_id: callId,
            type: 'progress',
            payload: expect.objectContaining({ step: 'Buffered' })
        }))
    })
  })
})