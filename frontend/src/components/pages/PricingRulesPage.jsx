import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function PricingRulesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Pricing Rules</h1>
        <p className="text-muted-foreground">
          Configure pricing rules and rates
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Pricing Configuration</CardTitle>
          <CardDescription>
            This page will contain pricing rules management
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Pricing rules management features coming soon...
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

