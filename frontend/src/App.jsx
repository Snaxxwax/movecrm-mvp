import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Toaster } from 'sonner'
import { AuthProvider, useAuth } from '@/hooks/useAuth'
import { TenantProvider } from '@/hooks/useTenant'

// Layout Components
import DashboardLayout from '@/components/layout/DashboardLayout'
import AuthLayout from '@/components/layout/AuthLayout'

// Page Components
import LoginPage from '@/components/pages/LoginPage'
import DashboardPage from '@/components/pages/DashboardPage'
import QuotesPage from '@/components/pages/QuotesPage'
import QuoteDetailPage from '@/components/pages/QuoteDetailPage'
import CustomersPage from '@/components/pages/CustomersPage'
import PricingRulesPage from '@/components/pages/PricingRulesPage'
import BrandSettingsPage from '@/components/pages/BrandSettingsPage'
import ItemCatalogPage from '@/components/pages/ItemCatalogPage'

import './App.css'

// Protected Route Component
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }
  
  if (!user) {
    return <Navigate to="/login" replace />
  }
  
  return children
}

// Public Route Component (redirect if authenticated)
function PublicRoute({ children }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }
  
  if (user) {
    return <Navigate to="/dashboard" replace />
  }
  
  return children
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={
        <PublicRoute>
          <AuthLayout>
            <LoginPage />
          </AuthLayout>
        </PublicRoute>
      } />
      
      {/* Protected Routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <DashboardLayout>
            <DashboardPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/quotes" element={
        <ProtectedRoute>
          <DashboardLayout>
            <QuotesPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/quotes/:id" element={
        <ProtectedRoute>
          <DashboardLayout>
            <QuoteDetailPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/customers" element={
        <ProtectedRoute>
          <DashboardLayout>
            <CustomersPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/pricing-rules" element={
        <ProtectedRoute>
          <DashboardLayout>
            <PricingRulesPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/item-catalog" element={
        <ProtectedRoute>
          <DashboardLayout>
            <ItemCatalogPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/settings" element={
        <ProtectedRoute>
          <DashboardLayout>
            <BrandSettingsPage />
          </DashboardLayout>
        </ProtectedRoute>
      } />
      
      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      
      {/* 404 fallback */}
      <Route path="*" element={
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
            <p className="text-gray-600 mb-4">Page not found</p>
            <a href="/dashboard" className="text-primary hover:underline">
              Return to Dashboard
            </a>
          </div>
        </div>
      } />
    </Routes>
  )
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <TenantProvider>
          <div className="min-h-screen bg-background">
            <AppRoutes />
            <Toaster />
          </div>
        </TenantProvider>
      </AuthProvider>
    </Router>
  )
}

export default App

