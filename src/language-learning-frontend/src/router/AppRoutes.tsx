import { Navigate, Route, Routes } from 'react-router'
import { useAuth } from '../auth/useAuth'
import AppLayout from '../components/layout/AppLayout'
import AdminPage from '../pages/admin/AdminPage'
import LoginPage from '../pages/auth/LoginPage'
import LessonPage from '../pages/lessons/LessonPage'
import LessonsPage from '../pages/lessons/LessonsPage'
import StatisticsPage from '../pages/statistics/StatisticsPage'
import { routes } from './routes'

export default function AppRoutes() {
  const { isAuthenticated, session } = useAuth()
  const isAdmin = session?.role === 'admin'

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path={routes.login} element={<LoginPage />} />
        <Route path={routes.register} element={<LoginPage />} />
        <Route path="*" element={<Navigate replace to={routes.login} />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path={routes.lessons} element={<LessonsPage />} />
        <Route path={routes.lesson} element={<LessonPage />} />
        <Route path={routes.statistics} element={<StatisticsPage />} />
        <Route
          path={routes.admin}
          element={isAdmin ? <AdminPage /> : <Navigate replace to={routes.lessons} />}
        />
        <Route path="*" element={<Navigate replace to={routes.lessons} />} />
      </Route>
    </Routes>
  )
}
