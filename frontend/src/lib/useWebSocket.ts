import { useEffect, useRef, useCallback, useState } from 'react'
import { useAvatarStore } from '../stores/avatarStore'

interface WebSocketConfig {
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

export function useWebSocket(config: WebSocketConfig) {
  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  const {
    setEmotion,
    setIsSpeaking,
    setVisemes,
    addMessage,
    setLoading
  } = useAvatarStore()

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/avatar`

    console.log('Connecting to WebSocket:', wsUrl)

    try {
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        config.onConnect?.()
      }

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        config.onDisconnect?.()
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        config.onError?.(error)
      }

      wsRef.current.onmessage = async (event) => {
        const data = JSON.parse(event.data)
        handleMessage(data)
      }
    } catch (error) {
      console.error('Failed to connect:', error)
    }
  }, [config])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const handleMessage = useCallback(async (data: any) => {
    switch (data.type) {
      case 'greeting':
        addMessage({
          role: 'assistant',
          content: data.message,
        })
        break

      case 'emotion_detected':
        setEmotion(data.emotion)
        break

      case 'response_text':
        setLoading(false)
        addMessage({
          role: 'assistant',
          content: data.text,
        })
        break

      case 'lip_sync_data':
        setVisemes(data.visemes)
        break

      case 'audio_data':
        setIsSpeaking(true)
        await playAudio(data.audio)
        setIsSpeaking(false)
        break

      case 'response_complete':
        setIsSpeaking(false)
        setLoading(false)
        break

      case 'error':
        setLoading(false)
        addMessage({
          role: 'assistant',
          content: `Error: ${data.message}`,
        })
        break
    }
  }, [addMessage, setEmotion, setIsSpeaking, setLoading, setVisemes])

  const playAudio = async (base64Audio: string) => {
    try {
      // Initialize AudioContext if needed
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext()
      }

      // Decode base64 to binary
      const binaryString = atob(base64Audio)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }

      // Decode audio data
      const audioBuffer = await audioContextRef.current.decodeAudioData(bytes.buffer)

      // Play audio
      const source = audioContextRef.current.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContextRef.current.destination)
      source.start()

      // Wait for audio to finish
      return new Promise<void>((resolve) => {
        source.onended = () => resolve()
      })
    } catch (error) {
      console.error('Error playing audio:', error)
    }
  }

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // Add user message to store
      if (message.type === 'text_input' || message.type === 'transcription') {
        addMessage({
          role: 'user',
          content: message.text,
        })
        setLoading(true)
      }

      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected')
    }
  }, [addMessage, setLoading])

  // Auto-connect on mount
  useEffect(() => {
    connect()
    return () => disconnect()
  }, [])

  return {
    isConnected,
    sendMessage,
    connect,
    disconnect,
  }
}
