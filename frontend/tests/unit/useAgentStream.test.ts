import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAgentStream } from '../../src/composables/useAgentStream'

let lastEventSource: MockEventSource | null = null

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

global.EventSource = MockEventSource as any

describe('useAgentStream', () => {
  beforeEach(() => {
    lastEventSource = null
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

  it('starts streaming and connects to EventSource', async () => {
    const { state, runTool } = useAgentStream()
    
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
        body: JSON.stringify({ arg1: 'val1' })
      })
    )
  })

  it('updates progress on message', async () => {
    const { state, runTool } = useAgentStream()
    
    runTool('test_tool')
    
    await vi.waitFor(() => expect(state.status).toBe('connected'))
    
    lastEventSource?.triggerMessage({
      type: 'progress',
      payload: { step: 'Working', pct: 50, log: 'Halfway there' }
    })

    expect(state.currentStep).toBe('Working')
    expect(state.progressPct).toBe(50)
    expect(state.logs).toContain('Halfway there')
  })

  it('handles completion result', async () => {
    const { state, runTool } = useAgentStream()
    
    runTool('test_tool')
    await vi.waitFor(() => expect(state.status).toBe('connected'))
    
    const es = lastEventSource
    es?.triggerMessage({
      type: 'result',
      payload: { data: 'final-result' }
    })

    expect(state.status).toBe('completed')
    expect(state.result).toEqual({ data: 'final-result' })
    expect(state.isStreaming).toBe(false)
    expect(es?.close).toHaveBeenCalled()
  })

  it('handles errors from stream', async () => {
    const { state, runTool } = useAgentStream()
    
    runTool('test_tool')
    await vi.waitFor(() => expect(state.status).toBe('connected'))
    
    const es = lastEventSource
    es?.triggerMessage({
      type: 'error',
      payload: { detail: 'Something went wrong' }
    })

    expect(state.status).toBe('error')
    expect(state.error).toBe('Something went wrong')
    expect(state.isStreaming).toBe(false)
    expect(es?.close).toHaveBeenCalled()
  })
})