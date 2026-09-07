import { useState } from 'react'
import { Navigate, Route, Routes } from 'react-router'
import { Toaster } from 'sonner'
import LessonPage from './pages/LessonPage'
import LessonsPage from './pages/LessonsPage'
import LoginPage from './pages/LoginPage'
import { routes } from './routes'
import Sidebar from './ui/Sidebar'
import Topbar from './ui/Topbar'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => localStorage.getItem('slep-learning-authenticated') === 'true',
  )

  const logIn = () => {
    localStorage.setItem('slep-learning-authenticated', 'true')
    setIsAuthenticated(true)
  }

  const logOut = () => {
    localStorage.removeItem('slep-learning-authenticated')
    setIsAuthenticated(false)
  }

  if (!isAuthenticated) {
    return (
      <>
        <Routes>
          <Route path={routes.login} element={<LoginPage onLogIn={logIn} />} />
          <Route path="*" element={<Navigate replace to={routes.login} />} />
        </Routes>
        <Toaster richColors theme="dark" position="top-right" />
      </>
    )
  }

  return (
    <div className="grid min-h-screen grid-rows-[auto_1fr] bg-[radial-gradient(circle_at_top_left,rgba(52,211,153,0.12),transparent_28%),radial-gradient(circle_at_top_right,rgba(59,130,246,0.13),transparent_30%),linear-gradient(180deg,#0c121c,#080c12)]">
      <Topbar onLogOut={logOut} />
      <div className="grid min-h-0 grid-cols-[236px_minmax(0,1fr)] max-[800px]:grid-cols-1">
        <Sidebar />
        <main className="min-w-0 p-6 max-[800px]:p-5">
          <Routes>
            <Route path={routes.lessons} element={<LessonsPage />} />
            <Route path={routes.lesson} element={<LessonPage />} />
            <Route path="*" element={<Navigate replace to={routes.lessons} />} />
          </Routes>
        </main>
      </div>
      <Toaster richColors theme="dark" position="top-right" />
    </div>
  )
}

export default App
