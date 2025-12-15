import { useState, useRef, useCallback } from 'react'
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react'

// Web Speech API types (not available in all TS configs)
interface SpeechRecognitionResult {
  isFinal: boolean
  [index: number]: { transcript: string }
}

interface SpeechRecognitionResultList {
  [index: number]: SpeechRecognitionResult
}

interface SpeechRecognitionEventType {
  resultIndex: number
  results: SpeechRecognitionResultList
}

interface SpeechRecognitionErrorEventType {
  error: string
}

interface VoiceControlsProps {
  onVoiceInput: (transcript: string) => void
  disabled?: boolean
}

export function VoiceControls({ onVoiceInput, disabled }: VoiceControlsProps) {
  const [isListening, setIsListening] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [transcript, setTranscript] = useState('')
  const recognitionRef = useRef<unknown>(null)

  // Initialize Web Speech API (FREE - runs in browser)
  const startListening = useCallback(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in your browser. Please use Chrome or Edge.')
      return
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    const recognition = new SpeechRecognition()

    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onstart = () => {
      setIsListening(true)
      setTranscript('')
    }

    recognition.onresult = (event: SpeechRecognitionEventType) => {
      const current = event.resultIndex
      const result = event.results[current]
      const text = result[0].transcript

      setTranscript(text)

      // If final result, send to server
      if (result.isFinal) {
        onVoiceInput(text)
        setTranscript('')
      }
    }

    recognition.onerror = (event: SpeechRecognitionErrorEventType) => {
      console.error('Speech recognition error:', event.error)
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognitionRef.current = recognition
    recognition.start()
  }, [onVoiceInput])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      (recognitionRef.current as { stop: () => void }).stop()
      recognitionRef.current = null
    }
    setIsListening(false)
  }, [])

  const toggleMute = () => {
    setIsMuted(!isMuted)
    // In a real implementation, this would mute the audio output
  }

  return (
    <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Microphone Button */}
          <button
            onClick={isListening ? stopListening : startListening}
            disabled={disabled}
            className={`p-4 rounded-full transition ${
              isListening
                ? 'bg-red-500 text-white animate-pulse'
                : 'bg-databricks-red text-white hover:bg-databricks-orange'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            title={isListening ? 'Stop listening' : 'Start voice input'}
          >
            {isListening ? (
              <MicOff className="w-6 h-6" />
            ) : (
              <Mic className="w-6 h-6" />
            )}
          </button>

          {/* Volume Button */}
          <button
            onClick={toggleMute}
            className={`p-3 rounded-full transition ${
              isMuted
                ? 'bg-white/10 text-white/40'
                : 'bg-white/10 text-white hover:bg-white/20'
            }`}
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? (
              <VolumeX className="w-5 h-5" />
            ) : (
              <Volume2 className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Status/Transcript */}
        <div className="flex-1 ml-4">
          {isListening ? (
            <div className="text-white">
              <p className="text-sm text-white/60">Listening...</p>
              {transcript && (
                <p className="text-white mt-1">{transcript}</p>
              )}
            </div>
          ) : (
            <p className="text-white/40 text-sm">
              Click the microphone to start speaking (uses free Web Speech API)
            </p>
          )}
        </div>
      </div>

      {/* Voice Level Indicator */}
      {isListening && (
        <div className="mt-3 flex gap-1 justify-center">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="w-2 h-6 bg-databricks-red rounded-full animate-pulse"
              style={{
                animationDelay: `${i * 0.1}s`,
                height: `${Math.random() * 20 + 10}px`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  )
}
