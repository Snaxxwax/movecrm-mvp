import { http, HttpResponse } from 'msw'
import { createMockUser, createMockQuote } from '../test-utils'

const API_BASE = 'http://localhost:5000/api'

// Default mock data
const mockUser = createMockUser()
const mockQuotes = [
  createMockQuote({ id: '1', quote_number: 'Q202401001' }),
  createMockQuote({ id: '2', quote_number: 'Q202401002', status: 'approved' }),
  createMockQuote({ id: '3', quote_number: 'Q202401003', status: 'rejected' }),
]

export const handlers = [
  // Authentication endpoints
  http.get(`${API_BASE}/auth/me`, ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    const tenantHeader = request.headers.get('X-Tenant-Slug')
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return new HttpResponse(
        JSON.stringify({ error: 'Authentication required' }),
        { status: 401 }
      )
    }
    
    if (!tenantHeader) {
      return new HttpResponse(
        JSON.stringify({ error: 'Tenant not found' }),
        { status: 400 }
      )
    }
    
    return HttpResponse.json(mockUser)
  }),

  http.post(`${API_BASE}/auth/login`, async ({ request }) => {
    const body = await request.json()
    const { email, password } = body
    
    if (email === 'test@example.com' && password === 'Password123!') {
      return HttpResponse.json({
        token: 'mock-jwt-token',
        user: mockUser
      })
    }
    
    return new HttpResponse(
      JSON.stringify({ message: 'Invalid credentials' }),
      { status: 401 }
    )
  }),

  http.get(`${API_BASE}/auth/users`, ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    const tenantHeader = request.headers.get('X-Tenant-Slug')
    
    if (!authHeader || !tenantHeader) {
      return new HttpResponse(
        JSON.stringify({ error: 'Authentication required' }),
        { status: 401 }
      )
    }
    
    const url = new URL(request.url)
    const page = parseInt(url.searchParams.get('page') || '1')
    const perPage = parseInt(url.searchParams.get('per_page') || '20')
    const role = url.searchParams.get('role')
    
    let users = [
      mockUser,
      createMockUser({
        id: '2',
        email: 'staff@example.com',
        first_name: 'Staff',
        last_name: 'Member',
        role: 'staff'
      }),
      createMockUser({
        id: '3',
        email: 'customer@example.com',
        first_name: 'Customer',
        last_name: 'User',
        role: 'customer'
      })
    ]
    
    if (role) {
      users = users.filter(user => user.role === role)
    }
    
    const total = users.length
    const startIndex = (page - 1) * perPage
    const endIndex = startIndex + perPage
    const paginatedUsers = users.slice(startIndex, endIndex)
    
    return HttpResponse.json({
      users: paginatedUsers,
      total,
      pages: Math.ceil(total / perPage),
      current_page: page,
      per_page: perPage
    })
  }),

  http.post(`${API_BASE}/auth/users`, async ({ request }) => {
    const body = await request.json()
    const { email, first_name, last_name, role = 'customer' } = body
    
    // Simulate duplicate email check
    if (email === 'existing@example.com') {
      return new HttpResponse(
        JSON.stringify({ error: 'User with this email already exists' }),
        { status: 400 }
      )
    }
    
    const newUser = createMockUser({
      id: Date.now().toString(),
      email,
      first_name,
      last_name,
      role
    })
    
    return new HttpResponse(
      JSON.stringify(newUser),
      { status: 201 }
    )
  }),

  // Quotes endpoints
  http.get(`${API_BASE}/quotes/`, ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    const tenantHeader = request.headers.get('X-Tenant-Slug')
    
    if (!authHeader || !tenantHeader) {
      return new HttpResponse(
        JSON.stringify({ error: 'Authentication required' }),
        { status: 401 }
      )
    }
    
    const url = new URL(request.url)
    const page = parseInt(url.searchParams.get('page') || '1')
    const perPage = parseInt(url.searchParams.get('per_page') || '20')
    const status = url.searchParams.get('status')
    const customerEmail = url.searchParams.get('customer_email')
    
    let filteredQuotes = [...mockQuotes]
    
    if (status) {
      filteredQuotes = filteredQuotes.filter(quote => quote.status === status)
    }
    
    if (customerEmail) {
      filteredQuotes = filteredQuotes.filter(quote => 
        quote.customer_email.toLowerCase().includes(customerEmail.toLowerCase())
      )
    }
    
    const total = filteredQuotes.length
    const startIndex = (page - 1) * perPage
    const endIndex = startIndex + perPage
    const paginatedQuotes = filteredQuotes.slice(startIndex, endIndex)
    
    return HttpResponse.json({
      quotes: paginatedQuotes,
      total,
      pages: Math.ceil(total / perPage),
      current_page: page,
      per_page: perPage
    })
  }),

  http.get(`${API_BASE}/quotes/:id`, ({ params }) => {
    const quote = mockQuotes.find(q => q.id === params.id)
    
    if (!quote) {
      return new HttpResponse(
        JSON.stringify({ error: 'Quote not found' }),
        { status: 404 }
      )
    }
    
    return HttpResponse.json({
      ...quote,
      items: [
        {
          id: '1',
          quote_id: quote.id,
          detected_name: 'Sofa',
          quantity: 1,
          cubic_feet: 35.5,
          labor_hours: 2.0,
          unit_price: 300.00,
          total_price: 300.00
        }
      ],
      media: []
    })
  }),

  http.post(`${API_BASE}/quotes/`, async ({ request }) => {
    const body = await request.json()
    
    const newQuote = createMockQuote({
      id: Date.now().toString(),
      quote_number: `Q${new Date().getFullYear()}${String(Date.now()).slice(-5)}`,
      ...body,
      status: 'pending',
      created_at: new Date().toISOString()
    })
    
    return new HttpResponse(
      JSON.stringify(newQuote),
      { status: 201 }
    )
  }),

  http.put(`${API_BASE}/quotes/:id`, async ({ params, request }) => {
    const body = await request.json()
    const quote = mockQuotes.find(q => q.id === params.id)
    
    if (!quote) {
      return new HttpResponse(
        JSON.stringify({ error: 'Quote not found' }),
        { status: 404 }
      )
    }
    
    const updatedQuote = { ...quote, ...body }
    return HttpResponse.json(updatedQuote)
  }),

  // Tenant endpoints
  http.get(`${API_BASE}/auth/tenants/current`, ({ request }) => {
    const tenantHeader = request.headers.get('X-Tenant-Slug')
    
    if (!tenantHeader) {
      return new HttpResponse(
        JSON.stringify({ error: 'Tenant not found' }),
        { status: 400 }
      )
    }
    
    return HttpResponse.json(mockUser.tenant)
  }),

  http.put(`${API_BASE}/auth/tenants/current`, async ({ request }) => {
    const body = await request.json()
    const updatedTenant = { ...mockUser.tenant, ...body }
    
    return HttpResponse.json(updatedTenant)
  })
]

// Error handlers for testing error scenarios
export const errorHandlers = [
  http.get(`${API_BASE}/auth/me`, () => {
    return new HttpResponse(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500 }
    )
  }),

  http.post(`${API_BASE}/auth/login`, () => {
    return new HttpResponse(
      JSON.stringify({ error: 'Service unavailable' }),
      { status: 503 }
    )
  }),

  http.get(`${API_BASE}/quotes/`, () => {
    return new HttpResponse(
      JSON.stringify({ error: 'Database connection failed' }),
      { status: 500 }
    )
  })
]