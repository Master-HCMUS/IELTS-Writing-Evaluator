import { useState } from 'react'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Login } from './Login'
import { Register } from './Register'

interface AuthModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  defaultMode?: 'login' | 'register'
}

export const AuthModal: React.FC<AuthModalProps> = ({
  open,
  onOpenChange,
  defaultMode = 'login'
}) => {
  const [mode, setMode] = useState<'login' | 'register'>(defaultMode)

  const handleSuccess = () => {
    onOpenChange(false)
  }

  const switchToRegister = () => setMode('register')
  const switchToLogin = () => setMode('login')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md p-0">
        {mode === 'login' ? (
          <Login onSwitchToRegister={switchToRegister} onSuccess={handleSuccess} />
        ) : (
          <Register onSwitchToLogin={switchToLogin} onSuccess={handleSuccess} />
        )}
      </DialogContent>
    </Dialog>
  )
}
