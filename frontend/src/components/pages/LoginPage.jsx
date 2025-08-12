import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2 } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

export default function LoginPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    tenantSlug: ''
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
    // Clear error when user starts typing
    if (error) setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    // Basic validation
    if (!formData.email || !formData.password || !formData.tenantSlug) {
      setError('All fields are required')
      setIsLoading(false)
      return
    }

    try {
      const result = await login(formData.email, formData.password, formData.tenantSlug)
      
      if (result.success) {
        navigate('/dashboard')
      } else {
        setError(result.error || 'Login failed')
      }
    } catch (err) {
      setError('An unexpected error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  // Demo credentials for testing
  const fillDemoCredentials = () => {
    setFormData({
      email: 'admin@demo.com',
      password: 'password123',
      tenantSlug: 'demo'
    })
  }

  return (
    <Card className="w-full">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl text-center">Sign in</CardTitle>
        <CardDescription className="text-center">
          Enter your credentials to access your MoveCRM dashboard
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="tenantSlug">Company Slug</Label>
            <Input
              id="tenantSlug"
              name="tenantSlug"
              type="text"
              placeholder="your-company"
              value={formData.tenantSlug}
              onChange={handleChange}
              disabled={isLoading}
              required
            />
            <p className="text-xs text-muted-foreground">
              Your company's unique identifier (e.g., "acme-movers")
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder="admin@yourcompany.com"
              value={formData.email}
              onChange={handleChange}
              disabled={isLoading}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              name="password"
              type="password"
              placeholder="Enter your password"
              value={formData.password}
              onChange={handleChange}
              disabled={isLoading}
              required
            />
          </div>

          <Button 
            type="submit" 
            className="w-full" 
            disabled={isLoading}
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Sign in
          </Button>

          {/* Demo credentials button for testing */}
          <div className="pt-4 border-t">
            <Button 
              type="button" 
              variant="outline" 
              className="w-full" 
              onClick={fillDemoCredentials}
              disabled={isLoading}
            >
              Use Demo Credentials
            </Button>
            <p className="text-xs text-muted-foreground text-center mt-2">
              For testing purposes only
            </p>
          </div>
        </form>

        <div className="mt-6 text-center text-sm text-muted-foreground">
          <p>
            Need help? Contact your system administrator or{' '}
            <a href="mailto:support@movecrm.com" className="text-primary hover:underline">
              support@movecrm.com
            </a>
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

