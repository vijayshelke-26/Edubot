import { useState } from 'react'
import api from '../api/client'

const domainColors = {
  programming: 'bg-brand-100 text-brand-800',
  mathematics: 'bg-violet-100 text-violet-800',
  science: 'bg-sky-100 text-sky-800',
  aptitude: 'bg-accent-100 text-accent-600',
  general: 'bg-line text-ink-soft',
}

function formatContent(text) {
  let html = text
    .replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br/>')
  return html
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user'
  const [feedback, setFeedback] = useState(message.feedback ?? null)
  const [submitting, setSubmitting] = useState(false)

  const sendFeedback = async (value) => {
    if (submitting || !message.id || typeof message.id !== 'number') return
    const next = feedback === value ? 0 : value
    setSubmitting(true)
    const previous = feedback
    setFeedback(next === 0 ? null : next)
    try {
      await api.post(`/chat/messages/${message.id}/feedback`, { feedback: next })
    } catch (err) {
      setFeedback(previous)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={`flex items-end gap-2 mb-4 animate-fade-up ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <span className="grid place-items-center h-8 w-8 rounded-full bg-brand-700 text-paper text-sm shrink-0 shadow-brand">
          🎓
        </span>
      )}
      <div
        className={`max-w-[80%] px-4 py-3 ${
          isUser
            ? 'bg-brand-700 text-paper rounded-2xl rounded-br-md shadow-brand'
            : 'bg-surface border border-line text-ink rounded-2xl rounded-bl-md shadow-card'
        }`}
      >
        {!isUser && message.detected_domain && message.detected_domain !== 'general' && (
          <div className="mb-1.5">
            <span
              className={`chip px-2 py-0.5 capitalize ${
                domainColors[message.detected_domain] || domainColors.general
              }`}
            >
              {message.detected_domain}
            </span>
          </div>
        )}
        <div
          className="chat-content text-sm leading-relaxed"
          dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
        />
        <div className="flex items-center justify-between gap-2 mt-1.5">
          <div
            className={`text-[0.7rem] ${
              isUser ? 'text-brand-100/80' : 'text-ink-faint'
            }`}
          >
            {new Date(message.created_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>
          {!isUser && typeof message.id === 'number' && (
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => sendFeedback(1)}
                disabled={submitting}
                aria-label="Helpful"
                title="Helpful"
                className={`text-sm px-1.5 py-0.5 rounded-lg transition-colors ${
                  feedback === 1
                    ? 'bg-brand-100 text-brand-700'
                    : 'text-ink-faint hover:text-brand-600 hover:bg-line/50'
                }`}
              >
                👍
              </button>
              <button
                type="button"
                onClick={() => sendFeedback(-1)}
                disabled={submitting}
                aria-label="Not helpful"
                title="Not helpful"
                className={`text-sm px-1.5 py-0.5 rounded-lg transition-colors ${
                  feedback === -1
                    ? 'bg-red-100 text-red-700'
                    : 'text-ink-faint hover:text-red-600 hover:bg-line/50'
                }`}
              >
                👎
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
