import Sidebar from '@/components/sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function SupplierRiskPage() {
  const suppliers = [
    {
      name: 'TechCorp Industries',
      rating: 3.2,
      reliability: 72,
      onTimeDelivery: 68,
      qualityScore: 75,
      status: 'warning',
    },
    {
      name: 'PowerTech Solutions',
      rating: 4.5,
      reliability: 92,
      onTimeDelivery: 95,
      qualityScore: 91,
      status: 'good',
    },
    {
      name: 'ElectroSupply Co',
      rating: 2.8,
      reliability: 65,
      onTimeDelivery: 60,
      qualityScore: 62,
      status: 'critical',
    },
    {
      name: 'ConnectTech Ltd',
      rating: 4.2,
      reliability: 88,
      onTimeDelivery: 90,
      qualityScore: 87,
      status: 'good',
    },
  ];

  const riskMetrics = [
    { label: 'Financial Stability', score: 65, color: 'bg-yellow-500' },
    { label: 'Delivery Performance', score: 72, color: 'bg-blue-500' },
    { label: 'Quality Consistency', score: 68, color: 'bg-orange-500' },
    { label: 'Compliance Records', score: 80, color: 'bg-green-500' },
  ];

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <main className="flex-1 overflow-auto">
        <div className="p-8 space-y-8">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-foreground">Supplier Risk Analysis</h1>
            <p className="text-foreground/60 mt-1">Supplier reliability and compliance ratings</p>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-500">3.8</div>
                  <p className="text-sm text-foreground/60 mt-2">Average Supplier Risk</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-500">12</div>
                  <p className="text-sm text-foreground/60 mt-2">Verified Suppliers</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-yellow-500">28</div>
                  <p className="text-sm text-foreground/60 mt-2">At-Risk Suppliers</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-500">8</div>
                  <p className="text-sm text-foreground/60 mt-2">Critical Suppliers</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Supplier Ratings */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle>Supplier Performance Rating</CardTitle>
              <CardDescription>Assessment of supplier metrics and reliability</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {suppliers.map((supplier) => (
                <div key={supplier.name} className="border-b border-border pb-4 last:border-b-0">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-foreground">{supplier.name}</h3>
                      <p className="text-sm text-foreground/60">Risk Rating: {supplier.rating.toFixed(1)}/5.0</p>
                    </div>
                    <span
                      className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${
                        supplier.status === 'good'
                          ? 'bg-green-500/20 text-green-500 border-green-500/30'
                          : supplier.status === 'warning'
                          ? 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30'
                          : 'bg-red-500/20 text-red-500 border-red-500/30'
                      }`}
                    >
                      {supplier.status === 'good' ? 'Verified' : supplier.status === 'warning' ? 'Warning' : 'Critical'}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <div className="text-sm text-foreground/60 mb-1">Reliability</div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${supplier.reliability}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-foreground mt-1">{supplier.reliability}%</div>
                    </div>
                    <div>
                      <div className="text-sm text-foreground/60 mb-1">On-Time Delivery</div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-green-500 rounded-full"
                          style={{ width: `${supplier.onTimeDelivery}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-foreground mt-1">{supplier.onTimeDelivery}%</div>
                    </div>
                    <div>
                      <div className="text-sm text-foreground/60 mb-1">Quality Score</div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-orange-500 rounded-full"
                          style={{ width: `${supplier.qualityScore}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-foreground mt-1">{supplier.qualityScore}%</div>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Risk Metrics */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle>Overall Supplier Risk Metrics</CardTitle>
              <CardDescription>Aggregated risk factors across supply chain</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {riskMetrics.map((metric) => (
                <div key={metric.label} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-foreground font-medium">{metric.label}</span>
                    <span className="text-foreground/60">{metric.score}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${metric.color}`}
                      style={{ width: `${metric.score}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Recommendations */}
          <Card className="bg-card border-border border-l-4 border-l-red-500">
            <CardHeader>
              <CardTitle className="text-lg">Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-foreground/80">
                <li className="flex items-start gap-3">
                  <span className="text-red-500 font-bold mt-1">1</span>
                  <span>Conduct audits for critical suppliers with risk ratings above 3.5</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-red-500 font-bold mt-1">2</span>
                  <span>Establish backup suppliers for components sourced from at-risk suppliers</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-red-500 font-bold mt-1">3</span>
                  <span>Implement contractual penalties for missed delivery deadlines</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-red-500 font-bold mt-1">4</span>
                  <span>Increase safety stock for high-risk supplier components</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
