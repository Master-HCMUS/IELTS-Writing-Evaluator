import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2 } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useTranslation } from 'react-i18next'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginForm = z.infer<typeof loginSchema>

interface LoginProps {
  onSwitchToRegister: () => void
  onSuccess?: () => void
}

export const Login: React.FC<LoginProps> = ({ onSwitchToRegister, onSuccess }) => {
  const { t } = useTranslation()
  const { signIn } = useAuth()
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    setLoading(true)
    setError('')

    try {
      const { error } = await signIn(data.email, data.password)

      if (error) {
        setError(error.message)
      } else {
        onSuccess?.()
      }
    } catch (err) {
      setError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold text-center">
          {t('auth.login.title', 'Sign In')}
        </CardTitle>
        <CardDescription className="text-center">
          {t('auth.login.description', 'Enter your credentials to access your account')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="email">{t('auth.email', 'Email')}</Label>
            <Input
              id="email"
              type="email"
              placeholder={t('auth.emailPlaceholder', 'Enter your email')}
              {...register('email')}
            />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">{t('auth.password', 'Password')}</Label>
            <Input
              id="password"
              type="password"
              placeholder={t('auth.passwordPlaceholder', 'Enter your password')}
              {...register('password')}
            />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {t('auth.login.button', 'Sign In')}
          </Button>
        </form>

        <div className="mt-4 text-center">
          <p className="text-sm text-muted-foreground">
            {t('auth.noAccount', "Don't have an account?")}{' '}
            <button
              type="button"
              onClick={onSwitchToRegister}
              className="text-primary hover:underline font-medium"
            >
              {t('auth.register.link', 'Sign up')}
            </button>
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
