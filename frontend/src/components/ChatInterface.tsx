import { useState, useRef, useEffect } from 'react'
import { useAvatarStore } from '../stores/avatarStore'
import { Send, Loader2, RefreshCw, Trash2 } from 'lucide-react'

interface ChatInterfaceProps {
  onSendMessage: (text: string) => void
  isConnected: boolean
  onConnect: () => void
  onDisconnect: () => void
}

export function ChatInterface({
  onSendMessage,
  isConnected,
  onConnect,
  onDisconnect,
}: ChatInterfaceProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages, isLoading, clearMessages } = useAvatarStore()

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && isConnected && !isLoading) {
      onSendMessage(input.trim())
      setInput('')
    }
  }

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: 'numeric',
      hour12: true,
    }).format(date)
  }

  return (
    <div className="h-full flex flex-col bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10">
      {/* Header */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <h2 className="text-white font-semibold">Chat</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={clearMessages}
            className="p-2 text-white/60 hover:text-white hover:bg-white/10 rounded-lg transition"
            title="Clear chat"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button
            onClick={isConnected ? onDisconnect : onConnect}
            className="p-2 text-white/60 hover:text-white hover:bg-white/10 rounded-lg transition"
            title={isConnected ? 'Disconnect' : 'Reconnect'}
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-white/40 mt-8">
            <p className="text-lg mb-2">Welcome to Databricks Avatar Assistant</p>
            <p className="text-sm">Ask me anything about Databricks!</p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {[
                'What is Databricks?',
                'Explain Delta Lake',
                'How does Spark work?',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => {
                    if (isConnected) {
                      onSendMessage(suggestion)
                    }
                  }}
                  className="px-3 py-1 bg-white/10 hover:bg-white/20 text-white/70 rounded-full text-sm transition"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex message-enter ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-databricks-red text-white'
                    : 'bg-white/10 text-white'
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                <p
                  className={`text-xs mt-1 ${
                    message.role === 'user' ? 'text-white/70' : 'text-white/40'
                  }`}
                >
                  {formatTime(message.timestamp)}
                </p>
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white/10 rounded-2xl px-4 py-3 flex items-center gap-2 text-white/60">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-white/10">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isConnected ? 'Type your message...' : 'Connecting...'}
            disabled={!isConnected || isLoading}
            className="flex-1 bg-white/10 text-white placeholder-white/40 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-databricks-red disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || !isConnected || isLoading}
            className="p-3 bg-databricks-red text-white rounded-xl hover:bg-databricks-orange transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  )
}
