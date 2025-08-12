import { createContext, useContext, useState, useEffect } from 'react'
import { useToast } from '@/hooks/use-toast'

const AuthContext = createContext({})

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  // API base URL - in production this would come from environment variables
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

  useEffect(() => {
    // Check for existing session on app load
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        setLoading(false)
        return
      }

      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        // Token is invalid, remove it
        localStorage.removeItem('auth_token')
        setUser(null)
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      localStorage.removeItem('auth_token')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password, tenantSlug) => {
    try {
      setLoading(true)
      
      // For now, we'll simulate login since SuperTokens integration would be complex
      // In production, this would integrate with SuperTokens
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Slug': tenantSlug
        },
        body: JSON.stringify({ email, password })
      })

      if (response.ok) {
        const data = await response.json()
        
        // Store token and user data
        localStorage.setItem('auth_token', data.token)
        localStorage.setItem('tenant_slug', tenantSlug)
        setUser(data.user)
        
        toast({
          title: "Login successful",
          description: "Welcome back!"
        })
        
        return { success: true }
      } else {
        const error = await response.json()
        toast({
          title: "Login failed",
          description: error.message || "Invalid credentials",
          variant: "destructive"
        })
        return { success: false, error: error.message }
      }
    } catch (error) {
      console.error('Login error:', error)
      toast({
        title: "Login failed",
        description: "Network error. Please try again.",
        variant: "destructive"
      })
      return { success: false, error: error.message }
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try {
      // Clear local storage
      localStorage.removeItem('auth_token')
      localStorage.removeItem('tenant_slug')
      
      // Clear user state
      setUser(null)
      
      toast({
        title: "Logged out",
        description: "You have been successfully logged out."
      })
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  const updateUser = (userData) => {
    setUser(prev => ({ ...prev, ...userData }))
  }

  const hasRole = (roles) => {
    if (!user) return false
    if (typeof roles === 'string') {
      return user.role === roles
    }
    return roles.includes(user.role)
  }

  const isAdmin = () => hasRole('admin')
  const isStaff = () => hasRole(['admin', 'staff'])

  const value = {
    user,
    loading,
    login,
    logout,
    updateUser,
    hasRole,
    isAdmin,
    isStaff,
    checkAuthStatus
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

