import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  FileText, 
  Users, 
  DollarSign, 
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Plus
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/hooks/use-toast'

// Mock data for demonstration
const mockStats = {
  total_quotes: 156,
  pending_quotes: 23,
  approved_quotes: 89,
  total_customers: 134,
  total_revenue: 245670.50,
  recent_quotes: [
    {
      id: '1',
      quote_number: 'Q202412001',
      customer_name: 'John Smith',
      customer_email: 'john@example.com',
      status: 'pending',
      total_amount: 2450.00,
      created_at: '2024-12-08T10:30:00Z'
    },
    {
      id: '2',
      quote_number: 'Q202412002',
      customer_name: 'Sarah Johnson',
      customer_email: 'sarah@example.com',
      status: 'approved',
      total_amount: 3200.00,
      created_at: '2024-12-08T09:15:00Z'
    },
    {
      id: '3',
      quote_number: 'Q202412003',
      customer_name: 'Mike Wilson',
      customer_email: 'mike@example.com',
      status: 'pending',
      total_amount: 1800.00,
      created_at: '2024-12-07T16:45:00Z'
    }
  ]
}

function StatCard({ title, value, icon: Icon, description, trend }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
        {trend && (
          <div className="flex items-center text-xs text-green-600 mt-1">
            <TrendingUp className="h-3 w-3 mr-1" />
            {trend}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function QuoteStatusBadge({ status }) {
  const variants = {
    pending: { variant: 'secondary', icon: Clock },
    approved: { variant: 'default', icon: CheckCircle },
    rejected: { variant: 'destructive', icon: AlertCircle },
    expired: { variant: 'outline', icon: AlertCircle }
  }

  const config = variants[status] || variants.pending
  const Icon = config.icon

  return (
    <Badge variant={config.variant} className="flex items-center gap-1">
      <Icon className="h-3 w-3" />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  )
}

export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const { user } = useAuth()
  const { toast } = useToast()

  useEffect(() => {
    loadDashboardStats()
  }, [])

  const loadDashboardStats = async () => {
    try {
      // In a real app, this would fetch from the API
      // For now, use mock data
      setTimeout(() => {
        setStats(mockStats)
        setLoading(false)
      }, 1000)
    } catch (error) {
      console.error('Failed to load dashboard stats:', error)
      toast({
        title: "Error",
        description: "Failed to load dashboard data",
        variant: "destructive"
      })
      setLoading(false)
    }
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Dashboard</h1>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="space-y-0 pb-2">
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded animate-pulse mb-2"></div>
                <div className="h-3 bg-gray-200 rounded animate-pulse"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back, {user?.first_name}! Here's what's happening with your business.
          </p>
        </div>
        <Button asChild>
          <Link to="/quotes">
            <Plus className="mr-2 h-4 w-4" />
            New Quote
          </Link>
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Quotes"
          value={stats.total_quotes}
          icon={FileText}
          description="All time quotes"
          trend="+12% from last month"
        />
        <StatCard
          title="Pending Quotes"
          value={stats.pending_quotes}
          icon={Clock}
          description="Awaiting approval"
        />
        <StatCard
          title="Total Customers"
          value={stats.total_customers}
          icon={Users}
          description="Active customers"
          trend="+8% from last month"
        />
        <StatCard
          title="Total Revenue"
          value={formatCurrency(stats.total_revenue)}
          icon={DollarSign}
          description="From approved quotes"
          trend="+15% from last month"
        />
      </div>

      {/* Recent Quotes */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Quotes</CardTitle>
            <CardDescription>
              Latest quote submissions and their status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.recent_quotes.map((quote) => (
                <div key={quote.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <Link 
                        to={`/quotes/${quote.id}`}
                        className="font-medium text-primary hover:underline"
                      >
                        {quote.quote_number}
                      </Link>
                      <QuoteStatusBadge status={quote.status} />
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {quote.customer_name} • {quote.customer_email}
                    </p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-sm font-medium">
                        {formatCurrency(quote.total_amount)}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(quote.created_at)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4">
              <Button variant="outline" asChild className="w-full">
                <Link to="/quotes">View All Quotes</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common tasks and shortcuts
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button asChild className="w-full justify-start">
              <Link to="/quotes">
                <Plus className="mr-2 h-4 w-4" />
                Create New Quote
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start">
              <Link to="/customers">
                <Users className="mr-2 h-4 w-4" />
                Manage Customers
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start">
              <Link to="/pricing-rules">
                <DollarSign className="mr-2 h-4 w-4" />
                Update Pricing Rules
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start">
              <Link to="/item-catalog">
                <FileText className="mr-2 h-4 w-4" />
                Manage Item Catalog
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

