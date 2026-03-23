import { useInterviewStore } from '@/lib/stores'

describe('Zustand Interview Store', () => {
  beforeEach(() => {
    useInterviewStore.getState().resetInterview()
  })

  it('should initialize with default values', () => {
    const state = useInterviewStore.getState()
    expect(state.currentInterviewId).toBeNull()
    expect(state.currentQuestionIndex).toBe(0)
    expect(state.answers).toEqual([])
    expect(state.isInterviewActive).toBe(false)
  })

  it('should set interview id correctly', () => {
    useInterviewStore.getState().setCurrentInterview('test-uuid')
    const state = useInterviewStore.getState()
    expect(state.currentInterviewId).toBe('test-uuid')
    expect(state.currentQuestionIndex).toBe(0)
    expect(state.answers).toEqual([])
  })
  
  it('should add answer and increment index', () => {
    useInterviewStore.getState().addAnswer(0, 'Test answer', 45)
    const state = useInterviewStore.getState()
    expect(state.answers).toHaveLength(1)
    expect(state.answers[0].answer).toBe('Test answer')
    expect(state.currentQuestionIndex).toBe(1)
  })

  it('should toggle interview active state', () => {
    useInterviewStore.getState().setInterviewActive(true)
    expect(useInterviewStore.getState().isInterviewActive).toBe(true)
  })
})
