import { renderHook, act, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '../useAuth'
import { server } from '../../test/mocks/server'
import { http, HttpResponse } from 'msw'

// Mock toast
const mockToast = vi.fn()
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: mockToast }),
}))

// Wrapper component for testing hooks
const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>

describe('useAuth', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    mockToast.mockClear()
  })

  describe('initialization', () => {
    it('should initialize with null user and loading true', () => {
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      expect(result.current.user).toBeNull()
      expect(result.current.loading).toBe(true)
    })

    it('should check auth status on mount when token exists', async () => {
      localStorage.setItem('auth_token', 'valid-token')
      
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.user).toBeTruthy()
      expect(result.current.user.email).toBe('test@example.com')
    })

    it('should handle invalid token on mount', async () => {
      localStorage.setItem('auth_token', 'invalid-token')
      
      // Mock invalid token response
      server.use(
        http.get('http://localhost:5000/api/auth/me', () => {
          return new HttpResponse(
            JSON.stringify({ error: 'Invalid token' }),
            { status: 401 }
          )
        })
      )
      
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.user).toBeNull()
      expect(localStorage.getItem('auth_token')).toBeNull()
    })

    it('should handle network error during auth check', async () => {
      localStorage.setItem('auth_token', 'valid-token')
      
      // Mock network error
      server.use(
        http.get('http://localhost:5000/api/auth/me', () => {
          return HttpResponse.error()
        })
      )
      
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      expect(result.current.user).toBeNull()
      expect(localStorage.getItem('auth_token')).toBeNull()
    })
  })

  describe('login', () => {
    it('should login successfully with valid credentials', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      let loginResult
      
      await act(async () => {
        loginResult = await result.current.login(
          'test@example.com',
          'Password123!',
          'test-company'
        )
      })
      
      expect(loginResult.success).toBe(true)
      expect(result.current.user).toBeTruthy()
      expect(result.current.user.email).toBe('test@example.com')
      expect(localStorage.getItem('auth_token')).toBe('mock-jwt-token')
      expect(localStorage.getItem('tenant_slug')).toBe('test-company')
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Login successful',
        description: 'Welcome back!',
      })
    })

    it('should handle login failure with invalid credentials', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      let loginResult
      
      await act(async () => {
        loginResult = await result.current.login(
          'wrong@example.com',
          'wrongpassword',
          'test-company'
        )
      })
      
      expect(loginResult.success).toBe(false)
      expect(loginResult.error).toBe('Invalid credentials')
      expect(result.current.user).toBeNull()
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Login failed',
        description: 'Invalid credentials',
        variant: 'destructive',
      })
    })

    it('should handle network error during login', async () => {
      // Mock network error
      server.use(
        http.post('http://localhost:5000/api/auth/login', () => {
          return HttpResponse.error()
        })
      )
      
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      let loginResult
      
      await act(async () => {
        loginResult = await result.current.login(
          'test@example.com',
          'Password123!',
          'test-company'
        )
      })
      
      expect(loginResult.success).toBe(false)
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Login failed',
        description: 'Network error. Please try again.',
        variant: 'destructive',
      })
    })

    it('should set loading state during login', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      // Start login (don't await immediately)
      const loginPromise = act(async () => {
        return result.current.login(
          'test@example.com',
          'Password123!',
          'test-company'
        )
      })
      
      // Check loading state is true during login
      expect(result.current.loading).toBe(true)
      
      await loginPromise
      
      // Check loading state is false after login
      expect(result.current.loading).toBe(false)
    })
  })

  describe('logout', () => {
    it('should logout and clear user data', async () => {
      // First login
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      await act(async () => {
        await result.current.login(
          'test@example.com',
          'Password123!',
          'test-company'
        )
      })
      
      expect(result.current.user).toBeTruthy()
      expect(localStorage.getItem('auth_token')).toBeTruthy()
      
      // Then logout
      await act(async () => {
        await result.current.logout()
      })
      
      expect(result.current.user).toBeNull()
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('tenant_slug')).toBeNull()
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Logged out',
        description: 'You have been successfully logged out.',
      })
    })
  })

  describe('role-based functions', () => {
    it('should check user roles correctly', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      await act(async () => {
        await result.current.login(
          'test@example.com',
          'Password123!',
          'test-company'
        )
      })
      
      // Test hasRole with string
      expect(result.current.hasRole('admin')).toBe(true)
      expect(result.current.hasRole('staff')).toBe(false)
      expect(result.current.hasRole('customer')).toBe(false)
      
      // Test hasRole with array
      expect(result.current.hasRole(['admin', 'staff'])).toBe(true)
      expect(result.current.hasRole(['staff', 'customer'])).toBe(false)
      
      // Test convenience methods
      expect(result.current.isAdmin()).toBe(true)
      expect(result.current.isStaff()).toBe(true) // admin is also staff
    })

    it('should return false for role checks when not logged in', () => {
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      expect(result.current.hasRole('admin')).toBe(false)
      expect(result.current.hasRole(['admin', 'staff'])).toBe(false)
      expect(result.current.isAdmin()).toBe(false)
      expect(result.current.isStaff()).toBe(false)
    })

    it('should handle staff role correctly', async () => {
      // Mock staff user response
      server.use(
        http.post('http://localhost:5000/api/auth/login', async () => {
          return HttpResponse.json({
            token: 'staff-token',
            user: {
              id: '2',
              email: 'staff@example.com',
              first_name: 'Staff',
              last_name: 'Member',
              role: 'staff',
              tenant: {
                id: '1',
                slug: 'test-company',
                name: 'Test Company',
              },
            },
          })
        })
      )
      
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      await act(async () => {
        await result.current.login(
          'staff@example.com',
          'Password123!',
          'test-company'
        )
      })
      
      expect(result.current.hasRole('staff')).toBe(true)
      expect(result.current.hasRole('admin')).toBe(false)
      expect(result.current.isAdmin()).toBe(false)
      expect(result.current.isStaff()).toBe(true)
    })
  })

  describe('updateUser', () => {
    it('should update user data', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      await act(async () => {
        await result.current.login(
          'test@example.com',
          'Password123!',
          'test-company'
        )
      })
      
      const originalUser = result.current.user
      
      act(() => {
        result.current.updateUser({
          first_name: 'Updated',
          last_name: 'Name',
        })
      })
      
      expect(result.current.user.first_name).toBe('Updated')
      expect(result.current.user.last_name).toBe('Name')
      expect(result.current.user.email).toBe(originalUser.email) // Should preserve other fields
    })
  })

  describe('checkAuthStatus', () => {
    it('should manually check auth status', async () => {
      localStorage.setItem('auth_token', 'valid-token')
      
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      // Wait for initial load
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
      
      // Clear user
      act(() => {
        result.current.updateUser(null)
      })
      
      // Manual auth check
      await act(async () => {
        await result.current.checkAuthStatus()
      })
      
      expect(result.current.user).toBeTruthy()
      expect(result.current.user.email).toBe('test@example.com')
    })
  })

  describe('error handling', () => {
    it('should throw error when used outside AuthProvider', () => {
      // Mock console.error to avoid noise in test output
      const originalError = console.error
      console.error = vi.fn()
      
      expect(() => {
        renderHook(() => useAuth()) // No wrapper
      }).toThrow('useAuth must be used within an AuthProvider')
      
      console.error = originalError
    })
  })

  describe('tenant integration', () => {
    it('should include tenant information in user data', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper })
      
      await act(async () => {
        await result.current.login(
          'test@example.com',
          'Password123!',
          'test-company'
        )
      })
      
      expect(result.current.user.tenant).toBeTruthy()
      expect(result.current.user.tenant.slug).toBe('test-company')
      expect(result.current.user.tenant.name).toBe('Test Moving Company')
    })
  })
})