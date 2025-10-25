import { useState, useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { AuthModal } from './AuthModal'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, loading } = useAuth()
  const location = useLocation()
  const [showAuthModal, setShowAuthModal] = useState(false)

  useEffect(() => {
    if (!loading && !user) {
      setShowAuthModal(true)
    }
  }, [loading, user])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!user) {
    return (
      <>
        <Navigate to="/" state={{ from: location }} replace />
        <AuthModal
          open={showAuthModal}
          onOpenChange={setShowAuthModal}
          defaultMode="login"
        />
      </>
    )
  }

  return <>{children}</>
}
