import { useState } from 'react'
import api from '../api/client'

const difficultyColor = {
  easy: 'bg-brand-100 text-brand-700',
  medium: 'bg-accent-100 text-accent-600',
  hard: 'bg-red-100 text-red-700',
}

const reasonLabel = {
  due_for_review: 'Review',
  weak_topic: 'Needs Practice',
  chatted_not_quizzed: 'From Your Chats',
  zpd_ready: 'New Topic',
  basics: 'Fundamental',
}

export default function Quiz() {
  const [stage, setStage] = useState('ready')
  const [questions, setQuestions] = useState([])
  const [topics, setTopics] = useState([])
  const [currentQ, setCurrentQ] = useState(0)
  const [answers, setAnswers] = useState({})
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const startQuiz = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/quiz/start')
      setTopics(res.data.topics)
      setQuestions(res.data.questions)
      setAnswers({})
      setCurrentQ(0)
      setStage('quiz')
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load quiz')
    } finally {
      setLoading(false)
    }
  }

  const selectAnswer = (idx, optionIndex) => {
    setAnswers(prev => ({ ...prev, [idx]: optionIndex }))
  }

  const submitQuiz = async () => {
    setLoading(true)
    try {
      const answerList = questions.map((q, i) => ({
        skill_id: q.skill_id,
        question_text: q.question,
        selected_index: answers[i] ?? -1,
        correct_index: q.correct_index,
        difficulty: q.difficulty,
        explanation: q.explanation || '',
      }))
      const res = await api.post('/quiz/submit', { answers: answerList })
      setResults(res.data)
      setStage('results')
    } catch (err) {
      setError('Failed to submit quiz')
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setStage('ready')
    setQuestions([])
    setTopics([])
    setResults(null)
    setError('')
  }

  // Ready screen
  if (stage === 'ready') {
    return (
      <div className="max-w-2xl mx-auto p-6 animate-fade-up">
        <h1 className="font-display text-3xl font-semibold text-ink mb-2">Adaptive Quiz</h1>
        <p className="text-ink-soft mb-6 max-w-xl">
          Questions are personalized from your chat history, weak areas, and spaced-repetition schedule.
        </p>
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">{error}</div>
        )}
        <div className="card p-10 text-center relative overflow-hidden">
          <div className="absolute -top-10 -right-10 h-40 w-40 rounded-full bg-accent-100/60 blur-2xl" />
          <div className="relative">
            <div className="text-6xl mb-5 inline-block animate-float">🧠</div>
            <h3 className="font-display text-2xl font-semibold text-ink mb-2">Smart Quiz</h3>
            <p className="text-sm text-ink-soft mb-5">The quiz adapts to your level using:</p>
            <div className="flex flex-wrap gap-2 justify-center mb-8">
              <span className="chip px-3 py-1.5 bg-brand-100 text-brand-700">Spaced Repetition</span>
              <span className="chip px-3 py-1.5 bg-violet-100 text-violet-700">Knowledge Tracing</span>
              <span className="chip px-3 py-1.5 bg-accent-100 text-accent-600">Your Chat Topics</span>
            </div>
            <button
              onClick={startQuiz}
              disabled={loading}
              className="btn-primary px-7 py-3 text-sm"
            >
              {loading ? 'Generating Quiz…' : 'Start Adaptive Quiz'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Quiz in progress
  if (stage === 'quiz') {
    const q = questions[currentQ]
    if (!q) return null

    return (
      <div className="max-w-2xl mx-auto p-6 animate-fade-in">
        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-sm font-medium text-ink-soft">
              Question {currentQ + 1} of {questions.length}
            </span>
            <div className="flex gap-2 mt-1.5">
              <span className={`chip px-2.5 py-0.5 capitalize ${difficultyColor[q.difficulty] || 'bg-line text-ink-soft'}`}>
                {q.difficulty}
              </span>
              <span className="chip px-2.5 py-0.5 bg-brand-50 text-brand-700 border border-brand-100">
                {q.skill_name || q.skill_id}
              </span>
            </div>
          </div>
          <button onClick={reset} className="text-sm font-medium text-ink-faint hover:text-red-600 transition-colors">
            Exit Quiz
          </button>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-line rounded-full h-2 mb-6 overflow-hidden">
          <div
            className="bg-gradient-to-r from-brand-500 to-brand-700 h-2 rounded-full transition-all duration-500"
            style={{ width: `${((currentQ + 1) / questions.length) * 100}%` }}
          />
        </div>

        <div className="card p-7">
          <h2 className="font-display text-xl font-medium text-ink mb-5 whitespace-pre-wrap leading-snug">{q.question}</h2>
          <div className="space-y-2.5">
            {q.options.map((option, idx) => {
              const selected = answers[currentQ] === idx
              return (
                <button
                  key={idx}
                  onClick={() => selectAnswer(currentQ, idx)}
                  className={`w-full text-left p-3.5 rounded-xl border text-sm transition-all flex items-start gap-3 ${
                    selected
                      ? 'border-brand-500 bg-brand-50 text-brand-800 shadow-card'
                      : 'border-line bg-surface-raised/50 hover:border-brand-300 hover:bg-surface text-ink'
                  }`}
                >
                  <span className={`grid place-items-center h-6 w-6 rounded-lg text-xs font-bold shrink-0 ${
                    selected ? 'bg-brand-700 text-paper' : 'bg-line text-ink-soft'
                  }`}>
                    {String.fromCharCode(65 + idx)}
                  </span>
                  <span className="pt-0.5">{option}</span>
                </button>
              )
            })}
          </div>
        </div>

        <div className="flex justify-between mt-6">
          <button
            onClick={() => setCurrentQ(prev => prev - 1)}
            disabled={currentQ === 0}
            className="btn-ghost px-5 py-2.5 text-sm disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          {currentQ < questions.length - 1 ? (
            <button
              onClick={() => setCurrentQ(prev => prev + 1)}
              className="btn-primary px-5 py-2.5 text-sm"
            >
              Next
            </button>
          ) : (
            <button
              onClick={submitQuiz}
              disabled={loading || Object.keys(answers).length < questions.length}
              className="btn-primary px-6 py-2.5 text-sm"
            >
              {loading ? 'Submitting…' : 'Submit Quiz'}
            </button>
          )}
        </div>
      </div>
    )
  }

  // Results
  if (stage === 'results' && results) {
    const pct = results.percentage
    const scoreColor = pct >= 80 ? 'text-brand-600' : pct >= 50 ? 'text-accent-500' : 'text-red-600'

    return (
      <div className="max-w-2xl mx-auto p-6 animate-fade-up">
        <div className="card p-8 text-center mb-6 relative overflow-hidden">
          <div className="absolute -top-12 left-1/2 -translate-x-1/2 h-40 w-40 rounded-full bg-brand-100/60 blur-2xl" />
          <div className="relative">
            <p className="chip px-3 py-1 bg-accent-100 text-accent-600 mb-3">Quiz Complete</p>
            <div className={`font-display text-5xl font-semibold ${scoreColor} mb-1`}>
              {results.score}<span className="text-ink-faint text-3xl">/{results.total}</span>
            </div>
            <p className="text-ink-soft text-sm">{pct}% correct</p>
          </div>
        </div>

        <div className="space-y-3">
          {results.results.map((r, idx) => {
            const q = questions[idx]
            return (
              <div
                key={idx}
                className={`p-4 rounded-2xl border ${
                  r.correct ? 'border-brand-200 bg-brand-50/70' : 'border-red-200 bg-red-50/70'
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className={`grid place-items-center h-7 w-7 rounded-full text-sm font-bold shrink-0 ${
                    r.correct ? 'bg-brand-600 text-paper' : 'bg-red-500 text-white'
                  }`}>
                    {r.correct ? '✓' : '✗'}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center flex-wrap gap-2 mb-1">
                      <span className="chip px-2 py-0.5 bg-brand-100 text-brand-700">
                        {r.skill_name}
                      </span>
                      <span className="text-xs text-ink-faint">
                        Mastery: {r.new_mastery} (P={r.p_learned})
                      </span>
                    </div>
                    <p className="text-sm font-medium text-ink">{q?.question}</p>
                    {!r.correct && (
                      <p className="text-xs text-ink-soft mt-1.5">
                        Correct answer: <span className="font-semibold">{String.fromCharCode(65 + r.correct_index)}.</span>{' '}
                        {q?.options[r.correct_index]}
                      </p>
                    )}
                    {r.explanation && (
                      <p className="text-xs text-ink-faint mt-1 italic">{r.explanation}</p>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={reset}
            className="btn-ghost flex-1 py-2.5 text-sm"
          >
            Back
          </button>
          <button
            onClick={startQuiz}
            className="btn-primary flex-1 py-2.5 text-sm"
          >
            Take Another Quiz
          </button>
        </div>
      </div>
    )
  }

  return null
}
