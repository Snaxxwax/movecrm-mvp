import { createContext, useContext, useState, useEffect } from 'react'
import { useAuth } from './useAuth'

const TenantContext = createContext({})

export function TenantProvider({ children }) {
  const [tenant, setTenant] = useState(null)
  const [loading, setLoading] = useState(true)
  const { user } = useAuth()

  // API base URL
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

  useEffect(() => {
    if (user) {
      loadTenantData()
    } else {
      setTenant(null)
      setLoading(false)
    }
  }, [user])

  const loadTenantData = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      const tenantSlug = localStorage.getItem('tenant_slug')
      
      if (!token || !tenantSlug) {
        setLoading(false)
        return
      }

      const response = await fetch(`${API_BASE_URL}/auth/tenants/current`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-Slug': tenantSlug,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const tenantData = await response.json()
        setTenant(tenantData)
      } else {
        console.error('Failed to load tenant data')
        setTenant(null)
      }
    } catch (error) {
      console.error('Error loading tenant data:', error)
      setTenant(null)
    } finally {
      setLoading(false)
    }
  }

  const updateTenant = async (updates) => {
    try {
      const token = localStorage.getItem('auth_token')
      const tenantSlug = localStorage.getItem('tenant_slug')
      
      const response = await fetch(`${API_BASE_URL}/auth/tenants/current`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-Slug': tenantSlug,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      })

      if (response.ok) {
        const updatedTenant = await response.json()
        setTenant(updatedTenant)
        return { success: true, data: updatedTenant }
      } else {
        const error = await response.json()
        return { success: false, error: error.message }
      }
    } catch (error) {
      console.error('Error updating tenant:', error)
      return { success: false, error: error.message }
    }
  }

  const getBrandColors = () => {
    if (!tenant?.brand_colors) {
      return {
        primary: '#2563eb',
        secondary: '#64748b'
      }
    }
    return tenant.brand_colors
  }

  const getSettings = () => {
    if (!tenant?.settings) {
      return {
        allow_customer_login: true,
        max_file_uploads: 5,
        max_file_size_mb: 50
      }
    }
    return tenant.settings
  }

  const value = {
    tenant,
    loading,
    updateTenant,
    getBrandColors,
    getSettings,
    reload: loadTenantData
  }

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  )
}

export function useTenant() {
  const context = useContext(TenantContext)
  if (!context) {
    throw new Error('useTenant must be used within a TenantProvider')
  }
  return context
}

