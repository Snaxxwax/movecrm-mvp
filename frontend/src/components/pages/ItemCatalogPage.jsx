import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function ItemCatalogPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Item Catalog</h1>
        <p className="text-muted-foreground">
          Manage your moving items catalog and pricing
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Item Catalog Management</CardTitle>
          <CardDescription>
            This page will contain item catalog management functionality
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Item catalog management features coming soon...
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

