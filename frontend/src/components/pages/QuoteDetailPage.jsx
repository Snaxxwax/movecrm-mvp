import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Edit, Download, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'

export default function QuoteDetailPage() {
  const { id } = useParams()
  const [quote, setQuote] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadQuote()
  }, [id])

  const loadQuote = async () => {
    // Mock quote data
    setTimeout(() => {
      setQuote({
        id: id,
        quote_number: 'Q202412001',
        customer_name: 'John Smith',
        customer_email: 'john@example.com',
        customer_phone: '(555) 123-4567',
        status: 'pending',
        total_amount: 2450.00,
        created_at: '2024-12-08T10:30:00Z',
        pickup_address: '123 Main St, City, State 12345',
        delivery_address: '456 Oak Ave, City, State 12345',
        move_date: '2024-12-15',
        notes: 'Customer needs help with packing fragile items.',
        items: [
          { name: 'Sofa', quantity: 1, cubic_feet: 35, price: 525 },
          { name: 'Dining Table', quantity: 1, cubic_feet: 25, price: 375 },
          { name: 'Chairs', quantity: 4, cubic_feet: 8, price: 120 },
          { name: 'Refrigerator', quantity: 1, cubic_feet: 45, price: 675 }
        ]
      })
      setLoading(false)
    }, 1000)
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardContent className="p-6">
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-4 bg-gray-200 rounded animate-pulse"></div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/quotes">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Quotes
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{quote.quote_number}</h1>
            <p className="text-muted-foreground">Quote details and items</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Download PDF
          </Button>
          <Button>
            <Send className="mr-2 h-4 w-4" />
            Send to Customer
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Quote Information */}
        <Card>
          <CardHeader>
            <CardTitle>Quote Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Status:</span>
              <Badge variant="secondary">{quote.status.charAt(0).toUpperCase() + quote.status.slice(1)}</Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Amount:</span>
              <span className="font-semibold">{formatCurrency(quote.total_amount)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Created:</span>
              <span>{new Date(quote.created_at).toLocaleDateString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Move Date:</span>
              <span>{new Date(quote.move_date).toLocaleDateString()}</span>
            </div>
          </CardContent>
        </Card>

        {/* Customer Information */}
        <Card>
          <CardHeader>
            <CardTitle>Customer Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <span className="text-muted-foreground">Name:</span>
              <p className="font-medium">{quote.customer_name}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Email:</span>
              <p>{quote.customer_email}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Phone:</span>
              <p>{quote.customer_phone}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Addresses */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Pickup Address</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{quote.pickup_address}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Delivery Address</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{quote.delivery_address}</p>
          </CardContent>
        </Card>
      </div>

      {/* Items */}
      <Card>
        <CardHeader>
          <CardTitle>Items</CardTitle>
          <CardDescription>Items included in this quote</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {quote.items.map((item, index) => (
              <div key={index} className="flex justify-between items-center p-3 border rounded">
                <div>
                  <p className="font-medium">{item.name}</p>
                  <p className="text-sm text-muted-foreground">
                    Quantity: {item.quantity} • {item.cubic_feet} cu ft each
                  </p>
                </div>
                <span className="font-semibold">{formatCurrency(item.price)}</span>
              </div>
            ))}
            <Separator />
            <div className="flex justify-between items-center text-lg font-semibold">
              <span>Total:</span>
              <span>{formatCurrency(quote.total_amount)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notes */}
      {quote.notes && (
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{quote.notes}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

