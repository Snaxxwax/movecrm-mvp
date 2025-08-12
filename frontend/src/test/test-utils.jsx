import { render } from '@testing-library/react'
import { AuthProvider } from '@/hooks/useAuth'
import { Toaster } from '@/components/ui/sonner'
import { BrowserRouter } from 'react-router-dom'

// Test wrapper that provides all necessary providers
export function TestWrapper({ children }) {
  return (
    <BrowserRouter>
      <AuthProvider>
        {children}
        <Toaster />
      </AuthProvider>
    </BrowserRouter>
  )
}

// Custom render function that includes providers
export function renderWithProviders(ui, options = {}) {
  return render(ui, {
    wrapper: TestWrapper,
    ...options,
  })
}

// Mock user data factory
export const createMockUser = (overrides = {}) => ({
  id: '123e4567-e89b-12d3-a456-426614174000',
  email: 'test@example.com',
  first_name: 'John',
  last_name: 'Doe',
  role: 'admin',
  is_active: true,
  tenant: {
    id: '123e4567-e89b-12d3-a456-426614174001',
    slug: 'test-company',
    name: 'Test Moving Company',
    domain: 'test-company.movecrm.com',
    is_active: true,
  },
  ...overrides,
})

// Mock quote data factory
export const createMockQuote = (overrides = {}) => ({
  id: '123e4567-e89b-12d3-a456-426614174002',
  quote_number: 'Q202401001',
  status: 'pending',
  customer_email: 'customer@example.com',
  customer_name: 'Jane Customer',
  pickup_address: '123 Main St, City, State',
  delivery_address: '456 Oak Ave, City, State',
  move_date: '2024-07-01',
  total_cubic_feet: 150.0,
  total_labor_hours: 8.5,
  subtotal: 1275.00,
  tax_amount: 102.00,
  total_amount: 1377.00,
  created_at: '2024-01-15T10:00:00Z',
  expires_at: '2024-02-15T10:00:00Z',
  ...overrides,
})

// Mock API responses
export const mockApiResponse = (data, status = 200) => {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
  })
}

// Mock fetch for API calls
export const mockFetch = (responses = []) => {
  let callCount = 0
  
  return vi.fn().mockImplementation((url, options) => {
    const response = responses[callCount] || responses[responses.length - 1]
    callCount++
    
    if (typeof response === 'function') {
      return response(url, options)
    }
    
    return mockApiResponse(response)
  })
}

// Mock authentication state
export const mockAuthState = (user = null, loading = false) => {
  return {
    user,
    loading,
    login: vi.fn(),
    logout: vi.fn(),
    updateUser: vi.fn(),
    hasRole: vi.fn((roles) => {
      if (!user) return false
      if (typeof roles === 'string') return user.role === roles
      return roles.includes(user.role)
    }),
    isAdmin: vi.fn(() => user?.role === 'admin'),
    isStaff: vi.fn(() => ['admin', 'staff'].includes(user?.role)),
    checkAuthStatus: vi.fn(),
  }
}

// Mock tenant context
export const mockTenantState = (tenant = null) => {
  return {
    tenant,
    setTenant: vi.fn(),
    loading: false,
  }
}

// Utility to wait for async updates
export const waitForAsync = () => {
  return new Promise(resolve => setTimeout(resolve, 0))
}

// Mock window location
export const mockLocation = (pathname = '/', search = '') => {
  delete window.location
  window.location = {
    pathname,
    search,
    hash: '',
    href: `http://localhost${pathname}${search}`,
    origin: 'http://localhost',
    protocol: 'http:',
    host: 'localhost',
    hostname: 'localhost',
    port: '',
    assign: vi.fn(),
    replace: vi.fn(),
    reload: vi.fn(),
  }
}

// Custom matchers for testing
export const customMatchers = {
  toBeInTheDocument: (received) => {
    const pass = received && document.body.contains(received)
    return {
      message: () => `expected element ${pass ? 'not ' : ''}to be in the document`,
      pass,
    }
  },
}

// Mock components for testing isolation
export const MockComponents = {
  LoadingSpinner: () => <div data-testid="loading-spinner">Loading...</div>,
  ErrorMessage: ({ message }) => <div data-testid="error-message">{message}</div>,
  SuccessMessage: ({ message }) => <div data-testid="success-message">{message}</div>,
}

// API endpoint constants for tests
export const API_ENDPOINTS = {
  AUTH_ME: '/api/auth/me',
  AUTH_LOGIN: '/api/auth/login',
  AUTH_USERS: '/api/auth/users',
  QUOTES: '/api/quotes/',
  TENANTS_CURRENT: '/api/auth/tenants/current',
}

// Test data constants
export const TEST_DATA = {
  VALID_EMAIL: 'test@example.com',
  VALID_PASSWORD: 'Password123!',
  INVALID_EMAIL: 'invalid-email',
  TENANT_SLUG: 'test-company',
}

export * from '@testing-library/react'
export { userEvent } from '@testing-library/user-event'