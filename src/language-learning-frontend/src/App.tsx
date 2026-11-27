import { Toaster } from 'sonner'
import { AuthProvider } from './auth/AuthProvider'
import AppRoutes from './router/AppRoutes'

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
      <Toaster richColors theme="dark" position="top-right" />
    </AuthProvider>
  )
}

export default App
