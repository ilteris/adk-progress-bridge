import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskMonitor from '../../src/components/TaskMonitor.vue'
import * as streamComposables from '../../src/composables/useAgentStream'
import { reactive } from 'vue'

describe('TaskMonitor.vue', () => {
  let mockState: any
  let mockRunTool: any
  let mockStopTool: any
  let mockReset: any
  let mockSendInput: any

  beforeEach(() => {
    mockState = reactive({
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
    mockRunTool = vi.fn()
    mockStopTool = vi.fn()
    mockReset = vi.fn()
    mockSendInput = vi.fn()

    vi.spyOn(streamComposables, 'useAgentStream').mockReturnValue({
      state: mockState,
      runTool: mockRunTool,
      stopTool: mockStopTool,
      reset: mockReset,
      sendInput: mockSendInput
    })
  })

  it('renders initial state', () => {
    const wrapper = mount(TaskMonitor)
    expect(wrapper.text()).toContain('Task Monitor')
    expect(wrapper.text()).toContain('Idle')
    expect(wrapper.find('.progress-bar').attributes('aria-valuenow')).toBe('0')
    expect(wrapper.find('button.btn-primary').text()).toBe('Start Task')
  })

  it('calls runTool when Start Task is clicked', async () => {
    const wrapper = mount(TaskMonitor)
    
    // Default tool is long_audit
    await wrapper.find('button.btn-primary').trigger('click')
    expect(mockRunTool).toHaveBeenCalledWith('long_audit', expect.any(Object))
  })

  it('updates UI when progress changes', async () => {
    const wrapper = mount(TaskMonitor)
    
    mockState.currentStep = 'Analyzing'
    mockState.progressPct = 45
    mockState.logs = ['Started analysis']
    
    await wrapper.vm.$nextTick()
    
    expect(wrapper.text()).toContain('Analyzing')
    expect(wrapper.text()).toContain('45%')
    expect(wrapper.find('.progress-bar').attributes('style')).toContain('width: 45%')
    expect(wrapper.text()).toContain('Started analysis')
  })

  it('displays input request and sends response', async () => {
    const wrapper = mount(TaskMonitor)
    
    mockState.status = 'waiting_for_input'
    mockState.inputPrompt = 'Continue?'
    
    await wrapper.vm.$nextTick()
    
    expect(wrapper.text()).toContain('Agent Input Request')
    expect(wrapper.text()).toContain('Continue?')
    
    const input = wrapper.find('input[placeholder="Type your response..."]')
    await input.setValue('yes')
    await wrapper.find('button.btn-warning').trigger('click')
    
    expect(mockSendInput).toHaveBeenCalledWith('yes')
  })

  it('displays result on completion', async () => {
    const wrapper = mount(TaskMonitor)
    
    mockState.result = { summary: 'Done!' }
    mockState.status = 'completed'
    
    await wrapper.vm.$nextTick()
    
    expect(wrapper.text()).toContain('Final Result:')
    expect(wrapper.text()).toContain('"summary": "Done!"')
    expect(wrapper.find('.badge.bg-light').text()).toBe('Done')
  })

  it('disables inputs and shows Stop Task while streaming', async () => {
    const wrapper = mount(TaskMonitor)
    
    mockState.isStreaming = true
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('#toolSelect').attributes()).toHaveProperty('disabled')
    expect(wrapper.find('button.btn-danger').text()).toBe('Stop Task')
  })

  it('calls reset when Reset button is clicked', async () => {
    const wrapper = mount(TaskMonitor)
    await wrapper.find('button.btn-outline-secondary').trigger('click')
    expect(mockReset).toHaveBeenCalled()
  })
})
