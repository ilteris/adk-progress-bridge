import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskMonitor from '../../src/components/TaskMonitor.vue'
import * as streamComposables from '../../src/composables/useAgentStream'
import { reactive } from 'vue'

describe('TaskMonitor.vue', () => {
  let mockState: streamComposables.AgentState
  let mockRunTool: any
  let mockStopTool: any
  let mockReset: any

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
      useWS: false
    })
    mockRunTool = vi.fn()
    mockStopTool = vi.fn()
    mockReset = vi.fn()

    vi.spyOn(streamComposables, 'useAgentStream').mockReturnValue({
      state: mockState,
      runTool: mockRunTool,
      stopTool: mockStopTool,
      reset: mockReset
    })
  })

  it('renders initial state', () => {
    const wrapper = mount(TaskMonitor)
    expect(wrapper.text()).toContain('Task Monitor')
    expect(wrapper.text()).toContain('Idle')
    expect(wrapper.find('.progress-bar').attributes('aria-valuenow')).toBe('0')
    expect(wrapper.find('button.btn-primary').text()).toBe('Start Audit')
  })

  it('calls runTool when Start Audit is clicked', async () => {
    const wrapper = mount(TaskMonitor)
    const durationInput = wrapper.find('#duration')
    await durationInput.setValue(10)
    
    await wrapper.find('button.btn-primary').trigger('click')
    
    expect(mockRunTool).toHaveBeenCalledWith('long_audit', { duration: 10 })
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

  it('displays result on completion', async () => {
    const wrapper = mount(TaskMonitor)
    
    mockState.result = { summary: 'Done!' }
    mockState.status = 'completed'
    
    await wrapper.vm.$nextTick()
    
    expect(wrapper.text()).toContain('Final Result:')
    expect(wrapper.text()).toContain('"summary": "Done!"')
    expect(wrapper.find('.badge.bg-light').text()).toBe('Done')
  })

  it('displays error on failure', async () => {
    const wrapper = mount(TaskMonitor)
    
    mockState.error = 'Network error'
    mockState.status = 'error'
    
    await wrapper.vm.$nextTick()
    
    expect(wrapper.text()).toContain('Error: Network error')
    expect(wrapper.find('.badge.bg-danger').text()).toBe('Error')
  })

  it('disables inputs and shows Stop Task while streaming', async () => {
    const wrapper = mount(TaskMonitor)
    
    mockState.isStreaming = true
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('#duration').attributes()).toHaveProperty('disabled')
    expect(wrapper.find('button.btn-danger').text()).toBe('Stop Task')
    expect(wrapper.find('button.btn-outline-secondary').attributes()).toHaveProperty('disabled')
  })

  it('calls reset when Reset button is clicked', async () => {
    const wrapper = mount(TaskMonitor)
    await wrapper.find('button.btn-outline-secondary').trigger('click')
    expect(mockReset).toHaveBeenCalled()
  })
})