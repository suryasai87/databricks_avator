import { useState, useCallback } from 'react'
import { Avatar3D } from './components/Avatar3D'
import { ChatInterface } from './components/ChatInterface'
import { VoiceControls } from './components/VoiceControls'
import { EmotionIndicator } from './components/EmotionIndicator'
import { useWebSocket } from './lib/useWebSocket'
import { useAvatarStore } from './stores/avatarStore'

function App() {
  const [isConnected, setIsConnected] = useState(false)
  const { emotion, isSpeaking, visemes } = useAvatarStore()

  const { sendMessage, connect, disconnect } = useWebSocket({
    onConnect: () => setIsConnected(true),
    onDisconnect: () => setIsConnected(false),
  })

  const handleSendMessage = useCallback((text: string) => {
    sendMessage({
      type: 'text_input',
      text,
    })
  }, [sendMessage])

  const handleVoiceInput = useCallback((transcript: string) => {
    // Send transcription from Web Speech API (FREE)
    sendMessage({
      type: 'transcription',
      text: transcript,
    })
  }, [sendMessage])

  return (
    <div className="min-h-screen bg-gradient-to-br from-databricks-dark to-databricks-gray flex flex-col">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-sm border-b border-white/20 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-databricks-red rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">D</span>
            </div>
            <div>
              <h1 className="text-white text-xl font-semibold">Databricks Avatar Assistant</h1>
              <p className="text-white/60 text-sm">Your AI-powered guide to Databricks</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <EmotionIndicator emotion={emotion} />
            <div className={`px-3 py-1 rounded-full text-sm ${
              isConnected
                ? 'bg-green-500/20 text-green-400'
                : 'bg-red-500/20 text-red-400'
            }`}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex">
        {/* Avatar Section */}
        <div className="w-1/2 p-6 flex flex-col">
          <div className="flex-1 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 overflow-hidden relative">
            <Avatar3D
              visemeData={visemes}
              emotion={emotion}
              isSpeaking={isSpeaking}
            />

            {/* Speaking Indicator */}
            {isSpeaking && (
              <div className="absolute bottom-4 left-4 bg-green-500 text-white px-4 py-2 rounded-full text-sm flex items-center gap-2">
                <span className="w-2 h-2 bg-white rounded-full pulse"></span>
                Speaking...
              </div>
            )}
          </div>

          {/* Voice Controls */}
          <div className="mt-4">
            <VoiceControls
              onVoiceInput={handleVoiceInput}
              disabled={!isConnected}
            />
          </div>
        </div>

        {/* Chat Section */}
        <div className="w-1/2 p-6 pl-0">
          <ChatInterface
            onSendMessage={handleSendMessage}
            isConnected={isConnected}
            onConnect={connect}
            onDisconnect={disconnect}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white/5 border-t border-white/10 px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-white/40 text-sm">
          <span>Cost-Optimized Avatar - Edge-TTS + Foundation Models</span>
          <span>Powered by Databricks</span>
        </div>
      </footer>
    </div>
  )
}

export default App
