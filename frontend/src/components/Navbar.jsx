import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const links = [
  { to: '/chat', label: 'Chat' },
  { to: '/quiz', label: 'Quiz' },
  { to: '/progress', label: 'Progress' },
]

export default function Navbar() {
  const { user, logout } = useAuth()
  const initial = (user?.username || '?').charAt(0).toUpperCase()

  return (
    <nav className="sticky top-0 z-50 border-b border-line/80 bg-paper/80 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-4 flex items-center justify-between h-16">
        <div className="flex items-center gap-7">
          <NavLink to="/chat" className="flex items-center gap-2.5 group">
            <span className="grid place-items-center h-9 w-9 rounded-xl bg-brand-700 text-paper text-lg shadow-brand transition-transform group-hover:-rotate-6">
              🎓
            </span>
            <span className="font-display text-xl font-semibold text-ink tracking-tight">
              Edu<span className="text-brand-600">Bot</span>
            </span>
          </NavLink>
          <div className="hidden sm:flex items-center gap-1">
            {links.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `px-3.5 py-1.5 rounded-full text-sm font-semibold transition-all ${
                    isActive
                      ? 'bg-brand-700 text-paper shadow-brand'
                      : 'text-ink-soft hover:text-ink hover:bg-line/50'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2.5 pl-3 pr-1.5 py-1 rounded-full border border-line bg-surface/60">
            <span className="text-sm font-medium text-ink-soft max-w-[10rem] truncate">{user?.username}</span>
            <span className="grid place-items-center h-7 w-7 rounded-full bg-accent-300 text-ink text-xs font-bold">
              {initial}
            </span>
          </div>
          <button
            onClick={logout}
            className="text-sm font-medium text-ink-faint hover:text-brand-700 transition-colors px-2 py-1"
          >
            Logout
          </button>
        </div>
      </div>
      {/* Mobile nav row */}
      <div className="sm:hidden flex items-center gap-1 px-4 pb-2.5 -mt-1">
        {links.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex-1 text-center px-3 py-1.5 rounded-full text-sm font-semibold transition-all ${
                isActive
                  ? 'bg-brand-700 text-paper'
                  : 'text-ink-soft bg-surface/60 border border-line'
              }`
            }
          >
            {label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
