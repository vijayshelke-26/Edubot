import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const highlights = [
  { icon: '💬', title: 'Ask anything', text: 'Conversational tutoring across programming, math & science.' },
  { icon: '🧠', title: 'Adaptive quizzes', text: 'Questions tuned to your level with spaced repetition.' },
  { icon: '📈', title: 'See your growth', text: 'Track skill mastery as you learn, topic by topic.' },
]

export default function Login() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-4xl grid lg:grid-cols-2 gap-8 items-center">
        {/* Brand / story panel */}
        <div className="hidden lg:block animate-fade-up">
          <h1 className="font-display text-5xl leading-[1.05] text-ink mb-4">
            A patient tutor for<br />
            <span className="text-brand-700 italic">curious</span> minds.
          </h1>
          <p className="text-ink-soft text-lg leading-relaxed mb-8 max-w-md">
            EduBot meets you where you are and grows with you — explaining concepts at just the right depth.
          </p>
          <ul className="space-y-4">
            {highlights.map((h, i) => (
              <li
                key={h.title}
                className="flex items-start gap-3.5 animate-fade-up"
                style={{ animationDelay: `${150 + i * 90}ms` }}
              >
                <span className="grid place-items-center h-10 w-10 rounded-xl bg-surface border border-line shadow-card text-lg shrink-0">
                  {h.icon}
                </span>
                <div>
                  <p className="font-semibold text-ink">{h.title}</p>
                  <p className="text-sm text-ink-soft">{h.text}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Form panel */}
        <div className="w-full max-w-sm mx-auto animate-scale-in">
          <div className="text-center mb-6 lg:hidden">
            <div className="text-5xl mb-3 inline-block animate-float">🎓</div>
            <h1 className="font-display text-3xl font-semibold text-ink">EduBot</h1>
          </div>

          <form onSubmit={handleSubmit} className="card p-7">
            <h2 className="font-display text-2xl font-semibold text-ink mb-1">Welcome back</h2>
            <p className="text-sm text-ink-soft mb-6">Sign in to continue your learning.</p>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-ink mb-1.5">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="field px-3.5 py-2.5 text-sm"
                  placeholder="you@example.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-ink mb-1.5">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="field px-3.5 py-2.5 text-sm"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-6 py-2.5 text-sm"
            >
              {loading ? 'Signing in…' : 'Sign In'}
            </button>

            <p className="text-center text-sm text-ink-soft mt-5">
              Don't have an account?{' '}
              <Link to="/register" className="text-brand-700 font-semibold hover:text-brand-800 hover:underline underline-offset-2">
                Register
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}
