import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import api from '../api/client'

const masteryColors = {
  mastered: { bg: 'bg-brand-100', text: 'text-brand-800', bar: '#1F6B4C' },
  proficient: { bg: 'bg-sky-100', text: 'text-sky-700', bar: '#2E7DA6' },
  familiar: { bg: 'bg-accent-100', text: 'text-accent-600', bar: '#DDA017' },
  attempted: { bg: 'bg-orange-100', text: 'text-orange-700', bar: '#D9763E' },
  not_started: { bg: 'bg-line', text: 'text-ink-faint', bar: '#CDBFA0' },
}

const stats = [
  { key: 'attempted', label: 'Skills Attempted', color: 'text-brand-700' },
  { key: 'mastered', label: 'Mastered', color: 'text-brand-600' },
  { key: 'proficient', label: 'Proficient', color: 'text-sky-600' },
  { key: 'overall', label: 'Overall Score', color: 'text-accent-500' },
]

export default function Progress() {
  const [skills, setSkills] = useState([])
  const [history, setHistory] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState('All')

  useEffect(() => {
    Promise.all([
      api.get('/quiz/mastery'),
      api.get('/quiz/history'),
      api.get('/progress/summary'),
    ]).then(([masteryRes, historyRes, summaryRes]) => {
      setSkills(masteryRes.data.skills)
      setHistory(historyRes.data.attempts)
      setSummary(summaryRes.data)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-9 w-9 border-2 border-line border-t-brand-600"></div>
      </div>
    )
  }

  // Calculate stats
  const totalSkills = skills.length
  const masteredCount = skills.filter(s => s.mastery_level === 'mastered').length
  const proficientCount = skills.filter(s => s.mastery_level === 'proficient').length
  const attemptedCount = skills.filter(s => s.mastery_level !== 'not_started').length
  const overallPct = summary?.overall?.percentage || 0

  const statValues = {
    attempted: `${attemptedCount}/${totalSkills}`,
    mastered: masteredCount,
    proficient: proficientCount,
    overall: `${overallPct}%`,
  }

  // Categories
  const categories = ['All', ...new Set(skills.map(s => s.category))]
  const filteredSkills = selectedCategory === 'All'
    ? skills
    : skills.filter(s => s.category === selectedCategory)

  // Chart data
  const chartData = history
    .slice(0, 10)
    .reverse()
    .map((a, i) => ({
      name: `#${i + 1}`,
      score: Math.round((a.score / a.total) * 100),
    }))

  const barColor = (v) => (v >= 80 ? '#1F6B4C' : v >= 50 ? '#DDA017' : '#D9763E')

  return (
    <div className="max-w-5xl mx-auto p-6 animate-fade-up">
      <h1 className="font-display text-3xl font-semibold text-ink mb-1">Learning Progress</h1>
      <p className="text-ink-soft mb-6">Your mastery, charted topic by topic.</p>

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {stats.map((s, i) => (
          <div
            key={s.key}
            className="card p-5 text-center animate-fade-up"
            style={{ animationDelay: `${i * 70}ms` }}
          >
            <div className={`font-display text-3xl font-semibold ${s.color}`}>{statValues[s.key]}</div>
            <div className="text-xs font-medium text-ink-faint mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Quiz score trend */}
      {chartData.length > 0 && (
        <div className="card p-5 mb-6">
          <h3 className="text-sm font-bold uppercase tracking-wide text-ink-soft mb-4">Quiz Score Trend</h3>
          <ResponsiveContainer width="100%" height={190}>
            <BarChart data={chartData} margin={{ top: 4, right: 4, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E3DBC8" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#8C8470' }} axisLine={{ stroke: '#E3DBC8' }} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#8C8470' }} axisLine={false} tickLine={false} />
              <Tooltip
                formatter={(val) => [`${val}%`, 'Score']}
                cursor={{ fill: 'rgba(35,91,67,0.06)' }}
                contentStyle={{
                  background: '#FCFAF4',
                  border: '1px solid #E3DBC8',
                  borderRadius: '0.75rem',
                  fontSize: '12px',
                  boxShadow: '0 14px 30px -18px rgba(33,30,23,0.22)',
                }}
              />
              <Bar dataKey="score" radius={[6, 6, 0, 0]} maxBarSize={46}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={barColor(entry.score)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Skill mastery grid */}
      <div className="card p-5 mb-6">
        <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
          <h3 className="text-sm font-bold uppercase tracking-wide text-ink-soft">Skill Mastery</h3>
          <div className="flex gap-1.5 flex-wrap">
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1 text-xs font-semibold rounded-full transition-all ${
                  selectedCategory === cat
                    ? 'bg-brand-700 text-paper shadow-brand'
                    : 'bg-surface border border-line text-ink-soft hover:border-brand-300 hover:text-brand-700'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {filteredSkills.map(skill => {
            const colors = masteryColors[skill.mastery_level] || masteryColors.not_started
            return (
              <div key={skill.skill_id} className="flex items-center justify-between p-3 rounded-xl bg-surface-raised/50 border border-line/70 hover:border-line-strong transition-colors">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className={`chip px-2 py-0.5 capitalize whitespace-nowrap ${colors.bg} ${colors.text}`}>
                    {skill.mastery_level.replace('_', ' ')}
                  </span>
                  <span className="text-sm text-ink truncate">{skill.name}</span>
                </div>
                <div className="flex items-center gap-3 ml-2">
                  {skill.total_attempts > 0 && (
                    <span className="text-xs text-ink-faint tabular-nums">
                      {skill.correct_attempts}/{skill.total_attempts}
                    </span>
                  )}
                  <div className="w-16 bg-line rounded-full h-2 overflow-hidden">
                    <div
                      className="h-2 rounded-full transition-all duration-500"
                      style={{
                        width: `${skill.percentage}%`,
                        backgroundColor: colors.bar,
                      }}
                    />
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Mastery legend */}
      <div className="flex flex-wrap gap-4 justify-center text-xs text-ink-soft">
        {Object.entries(masteryColors).map(([level, colors]) => (
          <div key={level} className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: colors.bar }} />
            <span className="capitalize">{level.replace('_', ' ')}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
