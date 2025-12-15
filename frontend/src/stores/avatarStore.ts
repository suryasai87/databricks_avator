import { create } from 'zustand'

interface VisemeData {
  start: number
  end: number
  value: string
  blendShape: string
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  emotion?: string
}

interface AvatarState {
  // Avatar state
  emotion: string
  isSpeaking: boolean
  visemes: VisemeData[]

  // Chat state
  messages: Message[]
  isLoading: boolean

  // Actions
  setEmotion: (emotion: string) => void
  setIsSpeaking: (speaking: boolean) => void
  setVisemes: (visemes: VisemeData[]) => void
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void
  setLoading: (loading: boolean) => void
  clearMessages: () => void
}

export const useAvatarStore = create<AvatarState>((set) => ({
  // Initial state
  emotion: 'neutral',
  isSpeaking: false,
  visemes: [],
  messages: [],
  isLoading: false,

  // Actions
  setEmotion: (emotion) => set({ emotion }),

  setIsSpeaking: (isSpeaking) => set({ isSpeaking }),

  setVisemes: (visemes) => set({ visemes }),

  addMessage: (message) => set((state) => ({
    messages: [
      ...state.messages,
      {
        ...message,
        id: Math.random().toString(36).substring(7),
        timestamp: new Date(),
      },
    ],
  })),

  setLoading: (isLoading) => set({ isLoading }),

  clearMessages: () => set({ messages: [] }),
}))
