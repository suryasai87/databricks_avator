import { motion } from 'framer-motion'

interface EmotionIndicatorProps {
  emotion: string
}

const emotionConfig: Record<string, { emoji: string; color: string; label: string }> = {
  joy: { emoji: '😊', color: 'bg-green-500', label: 'Happy' },
  anger: { emoji: '😤', color: 'bg-red-500', label: 'Frustrated' },
  sadness: { emoji: '😢', color: 'bg-blue-500', label: 'Sad' },
  fear: { emoji: '😰', color: 'bg-purple-500', label: 'Worried' },
  surprise: { emoji: '😮', color: 'bg-orange-500', label: 'Surprised' },
  confusion: { emoji: '🤔', color: 'bg-yellow-500', label: 'Confused' },
  neutral: { emoji: '😐', color: 'bg-gray-500', label: 'Neutral' },
}

export function EmotionIndicator({ emotion }: EmotionIndicatorProps) {
  const config = emotionConfig[emotion] || emotionConfig.neutral

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      key={emotion}
      className={`flex items-center gap-2 px-3 py-1 rounded-full ${config.color}/20`}
    >
      <span className="text-lg">{config.emoji}</span>
      <span className="text-white/80 text-sm">{config.label}</span>
    </motion.div>
  )
}
