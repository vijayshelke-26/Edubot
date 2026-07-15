import { useState, useRef, useEffect } from 'react'
import api from '../api/client'
import MessageBubble from './MessageBubble'

const suggestions = ['What is recursion?', 'Explain OOP', 'How do loops work?', 'Quiz me!']

export default function ChatWindow() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const [showSidebar, setShowSidebar] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(scrollToBottom, [messages])
  useEffect(() => { inputRef.current?.focus() }, [])

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      const res = await api.get('/chat/sessions')
      setSessions(res.data.sessions)
      // Auto-load the most recent session
      if (res.data.sessions.length > 0) {
        const latest = res.data.sessions[0]
        loadSession(latest.id)
      }
    } catch (err) {
      console.error('Failed to load sessions', err)
    }
  }

  const loadSession = async (sid) => {
    try {
      const res = await api.get(`/chat/sessions/${sid}/messages`)
      setSessionId(sid)
      setMessages(res.data.messages)
      setShowSidebar(false)
    } catch (err) {
      console.error('Failed to load messages', err)
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setLoading(true)

    // Optimistic user message
    const tempUserMsg = {
      id: Date.now(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, tempUserMsg])

    try {
      const res = await api.post('/chat/message', {
        message: text,
        session_id: sessionId,
      })
      setSessionId(res.data.session_id)

      // Replace optimistic message with real one and add bot response
      setMessages(prev => [
        ...prev.slice(0, -1),
        res.data.user_message,
        res.data.bot_message,
      ])

      // Refresh sessions list if this is a new session
      if (!sessionId) {
        loadSessions()
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'bot',
          content: 'Sorry, something went wrong. Please try again.',
          created_at: new Date().toISOString(),
        },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const startNewSession = () => {
    setMessages([])
    setSessionId(null)
  }

  const formatDate = (isoString) => {
    const d = new Date(isoString)
    const today = new Date()
    if (d.toDateString() === today.toDateString()) return 'Today'
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    if (d.toDateString() === yesterday.toDateString()) return 'Yesterday'
    return d.toLocaleDateString()
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] sm:h-[calc(100vh-4rem)]">
      {/* Sidebar - Chat History */}
      <aside className={`${showSidebar ? 'block' : 'hidden'} md:flex w-72 bg-surface/60 border-r border-line flex-shrink-0 flex-col`}>
        <div className="p-3">
          <button
            onClick={startNewSession}
            className="btn-primary w-full py-2.5 text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Chat
          </button>
        </div>
        <div className="px-3 pb-1">
          <p className="text-[0.7rem] font-bold uppercase tracking-wider text-ink-faint">History</p>
        </div>
        <div className="flex-1 overflow-y-auto px-2 pb-3 space-y-1">
          {sessions.length === 0 ? (
            <p className="text-xs text-ink-faint text-center mt-6">No chats yet — say hello 👋</p>
          ) : (
            sessions.map(s => (
              <button
                key={s.id}
                onClick={() => loadSession(s.id)}
                className={`w-full text-left px-3 py-2.5 rounded-xl border transition-all ${
                  sessionId === s.id
                    ? 'bg-brand-50 border-brand-200'
                    : 'bg-transparent border-transparent hover:bg-line/40'
                }`}
              >
                <div className="flex items-center gap-2 text-sm font-medium text-ink truncate">
                  <span className="text-brand-600">💬</span> Chat #{s.id}
                </div>
                <div className="flex justify-between text-xs text-ink-faint mt-0.5 pl-6">
                  <span>{s.message_count} messages</span>
                  <span>{formatDate(s.started_at)}</span>
                </div>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="bg-paper/70 backdrop-blur-sm border-b border-line px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="md:hidden text-ink-soft hover:text-ink"
              aria-label="Toggle history"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <span className="grid place-items-center h-9 w-9 rounded-xl bg-brand-700 text-paper shadow-brand shrink-0">🎓</span>
            <div className="min-w-0">
              <h2 className="font-display text-lg font-semibold text-ink leading-tight">Chat with EduBot</h2>
              <p className="text-xs text-ink-faint truncate">
                Python · OOP · data structures · algorithms & more
              </p>
            </div>
          </div>
          <button
            onClick={startNewSession}
            className="btn-ghost text-sm px-3.5 py-1.5 hidden md:inline-flex"
          >
            New Chat
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-5">
          <div className="max-w-3xl mx-auto">
            {messages.length === 0 && (
              <div className="text-center mt-16 animate-fade-up">
                <div className="text-6xl mb-5 inline-block animate-float">🎓</div>
                <h3 className="font-display text-2xl font-semibold text-ink">Welcome to EduBot</h3>
                <p className="text-sm text-ink-soft mt-2 max-w-md mx-auto">
                  Ask me anything about programming — variables, loops, OOP, algorithms, and more.
                </p>
                <div className="flex flex-wrap gap-2 justify-center mt-6">
                  {suggestions.map((q) => (
                    <button
                      key={q}
                      onClick={() => setInput(q)}
                      className="px-4 py-2 bg-surface border border-line rounded-full text-sm font-medium text-ink-soft hover:border-brand-300 hover:text-brand-700 hover:-translate-y-0.5 shadow-card transition-all"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {loading && (
              <div className="flex justify-start mb-3 animate-fade-in">
                <div className="flex items-end gap-2">
                  <span className="grid place-items-center h-8 w-8 rounded-full bg-brand-700 text-paper text-sm shrink-0">🎓</span>
                  <div className="bg-surface border border-line rounded-2xl rounded-bl-md px-4 py-3 shadow-card">
                    <div className="flex gap-1.5">
                      <span className="w-2 h-2 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                      <span className="w-2 h-2 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                      <span className="w-2 h-2 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <form onSubmit={sendMessage} className="bg-paper/70 backdrop-blur-sm border-t border-line p-3">
          <div className="flex gap-2 max-w-3xl mx-auto items-center bg-surface-raised border border-line rounded-2xl shadow-card pl-4 pr-2 py-1.5 focus-within:border-brand-400 focus-within:ring-4 focus-within:ring-brand-500/15 transition-all">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask EduBot a question…"
              className="flex-1 bg-transparent text-sm text-ink placeholder:text-ink-faint focus:outline-none"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="btn-primary px-4 py-2 text-sm"
              aria-label="Send message"
            >
              <span className="hidden sm:inline">Send</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
