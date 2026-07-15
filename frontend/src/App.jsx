import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Navbar from './components/Navbar'
import Login from './pages/Login'
import Register from './pages/Register'
import Chat from './pages/Chat'
import Quiz from './pages/Quiz'
import Progress from './pages/Progress'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-9 w-9 border-2 border-line border-t-brand-600"></div>
      </div>
    )
  }
  return user ? children : <Navigate to="/login" />
}

function AppRoutes() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen">
      {user && <Navbar />}
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/chat" /> : <Login />} />
        <Route path="/register" element={user ? <Navigate to="/chat" /> : <Register />} />
        <Route path="/chat" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
        <Route path="/quiz" element={<ProtectedRoute><Quiz /></ProtectedRoute>} />
        <Route path="/progress" element={<ProtectedRoute><Progress /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to={user ? "/chat" : "/login"} />} />
      </Routes>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
