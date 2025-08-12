import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../../../test/test-utils'
import LoginPage from '../LoginPage'
import { useAuth } from '../../../hooks/useAuth'
import { server } from '../../../test/mocks/server'
import { http, HttpResponse } from 'msw'

// Mock the useAuth hook
vi.mock('../../../hooks/useAuth')

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('LoginPage', () => {
  const mockAuthState = {
    user: null,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
    hasRole: vi.fn(),
    isAdmin: vi.fn(),
    isStaff: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    useAuth.mockReturnValue(mockAuthState)
  })

  describe('rendering', () => {
    it('should render login form', () => {
      renderWithProviders(<LoginPage />)
      
      expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/company slug/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    it('should render welcome message and branding', () => {
      renderWithProviders(<LoginPage />)
      
      expect(screen.getByText(/welcome to movecrm/i)).toBeInTheDocument()
      expect(screen.getByText(/streamline your moving business/i)).toBeInTheDocument()
    })

    it('should show loading spinner when auth is loading', () => {
      useAuth.mockReturnValue({
        ...mockAuthState,
        loading: true,
      })
      
      renderWithProviders(<LoginPage />)
      
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })
  })

  describe('form validation', () => {
    it('should show validation errors for empty fields', async () => {
      const user = userEvent.setup()
      renderWithProviders(<LoginPage />)
      
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument()
        expect(screen.getByText(/password is required/i)).toBeInTheDocument()
        expect(screen.getByText(/company slug is required/i)).toBeInTheDocument()
      })
    })

    it('should show validation error for invalid email', async () => {
      const user = userEvent.setup()
      renderWithProviders(<LoginPage />)
      
      const emailInput = screen.getByLabelText(/email/i)
      await user.type(emailInput, 'invalid-email')
      
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(/invalid email address/i)).toBeInTheDocument()
      })
    })

    it('should show validation error for weak password', async () => {
      const user = userEvent.setup()
      renderWithProviders(<LoginPage />)
      
      const passwordInput = screen.getByLabelText(/password/i)
      await user.type(passwordInput, '123') // Too short
      
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(/password must be at least 6 characters/i)).toBeInTheDocument()
      })
    })

    it('should clear validation errors when fields are corrected', async () => {
      const user = userEvent.setup()
      renderWithProviders(<LoginPage />)
      
      // Submit empty form to trigger validation errors
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      })
      
      // Fill in email field
      const emailInput = screen.getByLabelText(/email/i)
      await user.type(emailInput, 'test@example.com')
      
      await waitFor(() => {
        expect(screen.queryByText(/email is required/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('login functionality', () => {
    it('should call login function with correct credentials', async () => {
      const user = userEvent.setup()
      const mockLogin = vi.fn().mockResolvedValue({ success: true })
      useAuth.mockReturnValue({
        ...mockAuthState,
        login: mockLogin,
      })
      
      renderWithProviders(<LoginPage />)
      
      // Fill in form
      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/password/i), 'Password123!')
      await user.type(screen.getByLabelText(/company slug/i), 'test-company')
      
      // Submit form
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith(
          'test@example.com',
          'Password123!',
          'test-company'
        )
      })
    })

    it('should navigate to dashboard on successful login', async () => {
      const user = userEvent.setup()
      const mockLogin = vi.fn().mockResolvedValue({ success: true })
      useAuth.mockReturnValue({
        ...mockAuthState,
        login: mockLogin,
      })
      
      renderWithProviders(<LoginPage />)
      
      // Fill and submit form
      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/password/i), 'Password123!')
      await user.type(screen.getByLabelText(/company slug/i), 'test-company')
      await user.click(screen.getByRole('button', { name: /sign in/i }))
      
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
      })
    })

    it('should show error message on login failure', async () => {
      const user = userEvent.setup()
      const mockLogin = vi.fn().mockResolvedValue({
        success: false,
        error: 'Invalid credentials',
      })
      useAuth.mockReturnValue({
        ...mockAuthState,
        login: mockLogin,
      })
      
      renderWithProviders(<LoginPage />)
      
      // Fill and submit form
      await user.type(screen.getByLabelText(/email/i), 'wrong@example.com')
      await user.type(screen.getByLabelText(/password/i), 'wrongpassword')
      await user.type(screen.getByLabelText(/company slug/i), 'test-company')
      await user.click(screen.getByRole('button', { name: /sign in/i }))
      
      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
      })
      
      // Should not navigate on failure
      expect(mockNavigate).not.toHaveBeenCalled()
    })

    it('should show loading state during login', async () => {
      const user = userEvent.setup()
      let resolveLogin
      const mockLogin = vi.fn().mockImplementation(
        () => new Promise(resolve => (resolveLogin = resolve))
      )
      useAuth.mockReturnValue({
        ...mockAuthState,
        login: mockLogin,
      })
      
      renderWithProviders(<LoginPage />)
      
      // Fill and submit form
      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/password/i), 'Password123!')
      await user.type(screen.getByLabelText(/company slug/i), 'test-company')
      
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)
      
      // Check loading state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /signing in/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled()
      })
      
      // Resolve login
      resolveLogin({ success: true })
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /sign in/i })).not.toBeDisabled()
      })
    })

    it('should disable form during login attempt', async () => {
      const user = userEvent.setup()
      let resolveLogin
      const mockLogin = vi.fn().mockImplementation(
        () => new Promise(resolve => (resolveLogin = resolve))
      )
      useAuth.mockReturnValue({
        ...mockAuthState,
        login: mockLogin,
      })
      
      renderWithProviders(<LoginPage />)
      
      // Fill form
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const slugInput = screen.getByLabelText(/company slug/i)
      
      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'Password123!')
      await user.type(slugInput, 'test-company')
      
      // Submit form
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)
      
      // Check all inputs are disabled during login
      await waitFor(() => {
        expect(emailInput).toBeDisabled()
        expect(passwordInput).toBeDisabled()
        expect(slugInput).toBeDisabled()
        expect(submitButton).toBeDisabled()
      })
      
      // Resolve login
      resolveLogin({ success: true })
      
      // Check inputs are enabled again
      await waitFor(() => {
        expect(emailInput).not.toBeDisabled()
        expect(passwordInput).not.toBeDisabled()
        expect(slugInput).not.toBeDisabled()
        expect(submitButton).not.toBeDisabled()
      })
    })
  })

  describe('user experience', () => {
    it('should allow password visibility toggle', async () => {
      const user = userEvent.setup()
      renderWithProviders(<LoginPage />)
      
      const passwordInput = screen.getByLabelText(/password/i)
      const toggleButton = screen.getByRole('button', { name: /show password/i })
      
      // Initially password should be hidden
      expect(passwordInput.type).toBe('password')
      
      // Click toggle to show password
      await user.click(toggleButton)
      expect(passwordInput.type).toBe('text')
      
      // Click toggle to hide password again
      await user.click(toggleButton)
      expect(passwordInput.type).toBe('password')
    })

    it('should focus on email input on mount', () => {
      renderWithProviders(<LoginPage />)
      
      const emailInput = screen.getByLabelText(/email/i)
      expect(emailInput).toHaveFocus()
    })

    it('should allow form submission via Enter key', async () => {
      const user = userEvent.setup()
      const mockLogin = vi.fn().mockResolvedValue({ success: true })
      useAuth.mockReturnValue({
        ...mockAuthState,
        login: mockLogin,
      })
      
      renderWithProviders(<LoginPage />)
      
      // Fill form
      await user.type(screen.getByLabelText(/email/i), 'test@example.com')
      await user.type(screen.getByLabelText(/password/i), 'Password123!')
      await user.type(screen.getByLabelText(/company slug/i), 'test-company')
      
      // Press Enter in slug field
      await user.type(screen.getByLabelText(/company slug/i), '{Enter}')
      
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalled()
      })
    })
  })

  describe('redirect behavior', () => {
    it('should redirect to dashboard if already authenticated', () => {
      useAuth.mockReturnValue({
        ...mockAuthState,
        user: {
          id: '1',
          email: 'test@example.com',
          role: 'admin',
        },
        loading: false,
      })
      
      renderWithProviders(<LoginPage />)
      
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })

    it('should not redirect while loading', () => {
      useAuth.mockReturnValue({
        ...mockAuthState,
        user: null,
        loading: true,
      })
      
      renderWithProviders(<LoginPage />)
      
      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })

  describe('accessibility', () => {
    it('should have proper form labels and aria attributes', () => {
      renderWithProviders(<LoginPage />)
      
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const slugInput = screen.getByLabelText(/company slug/i)
      
      expect(emailInput).toHaveAttribute('type', 'email')
      expect(emailInput).toHaveAttribute('required')
      expect(passwordInput).toHaveAttribute('type', 'password')
      expect(passwordInput).toHaveAttribute('required')
      expect(slugInput).toHaveAttribute('required')
    })

    it('should associate error messages with form fields', async () => {
      const user = userEvent.setup()
      renderWithProviders(<LoginPage />)
      
      // Submit empty form to trigger validation
      await user.click(screen.getByRole('button', { name: /sign in/i }))
      
      await waitFor(() => {
        const emailInput = screen.getByLabelText(/email/i)
        const emailError = screen.getByText(/email is required/i)
        
        expect(emailInput).toHaveAttribute('aria-describedby')
        expect(emailError).toHaveAttribute('id', emailInput.getAttribute('aria-describedby'))
      })
    })

    it('should announce login errors to screen readers', async () => {
      const user = userEvent.setup()
      const mockLogin = vi.fn().mockResolvedValue({
        success: false,
        error: 'Invalid credentials',
      })
      useAuth.mockReturnValue({
        ...mockAuthState,
        login: mockLogin,
      })
      
      renderWithProviders(<LoginPage />)
      
      // Fill and submit form
      await user.type(screen.getByLabelText(/email/i), 'wrong@example.com')
      await user.type(screen.getByLabelText(/password/i), 'wrongpassword')
      await user.type(screen.getByLabelText(/company slug/i), 'test-company')
      await user.click(screen.getByRole('button', { name: /sign in/i }))
      
      await waitFor(() => {
        const errorMessage = screen.getByText(/invalid credentials/i)
        expect(errorMessage).toHaveAttribute('role', 'alert')
      })
    })
  })

  describe('responsive design', () => {
    it('should render mobile-friendly layout', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375, // Mobile width
      })
      
      renderWithProviders(<LoginPage />)
      
      // Should still render all essential elements
      expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })
  })
})