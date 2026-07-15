import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const steps = [
  { n: '01', title: 'Chat & explore', text: 'Ask questions and learn at your own pace.' },
  { n: '02', title: 'Take a quick quiz', text: 'EduBot finds your level automatically.' },
  { n: '03', title: 'Watch mastery grow', text: 'Your dashboard charts every skill.' },
]

export default function Register() {
  const { register } = useAuth()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(username, email, password)
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-4xl grid lg:grid-cols-2 gap-8 items-center">
        {/* Story panel */}
        <div className="hidden lg:block animate-fade-up order-2 lg:order-1">
          <div className="inline-flex items-center gap-2 chip bg-brand-100 text-brand-700 px-3 py-1 mb-6">
            <span className="h-1.5 w-1.5 rounded-full bg-brand-500" /> Free · Start learning in seconds
          </div>
          <h1 className="font-display text-5xl leading-[1.05] text-ink mb-8">
            Three steps to<br />
            <span className="text-brand-700 italic">smarter</span> study.
          </h1>
          <ul className="space-y-5">
            {steps.map((s, i) => (
              <li
                key={s.n}
                className="flex items-start gap-4 animate-fade-up"
                style={{ animationDelay: `${150 + i * 90}ms` }}
              >
                <span className="font-display text-2xl font-semibold text-accent-400 w-9 shrink-0">{s.n}</span>
                <div>
                  <p className="font-semibold text-ink">{s.title}</p>
                  <p className="text-sm text-ink-soft">{s.text}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Form panel */}
        <div className="w-full max-w-sm mx-auto animate-scale-in order-1 lg:order-2">
          <div className="text-center mb-6 lg:hidden">
            <div className="text-5xl mb-3 inline-block animate-float">🎓</div>
            <h1 className="font-display text-3xl font-semibold text-ink">EduBot</h1>
          </div>

          <form onSubmit={handleSubmit} className="card p-7">
            <h2 className="font-display text-2xl font-semibold text-ink mb-1">Create your account</h2>
            <p className="text-sm text-ink-soft mb-6">Begin your learning journey.</p>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-ink mb-1.5">Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="field px-3.5 py-2.5 text-sm"
                  placeholder="scholar123"
                  required
                />
              </div>
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
                  minLength={6}
                  required
                />
                <p className="text-xs text-ink-faint mt-1.5">At least 6 characters</p>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-6 py-2.5 text-sm"
            >
              {loading ? 'Creating account…' : 'Create Account'}
            </button>

            <p className="text-center text-sm text-ink-soft mt-5">
              Already have an account?{' '}
              <Link to="/login" className="text-brand-700 font-semibold hover:text-brand-800 hover:underline underline-offset-2">
                Sign In
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}
