import Sidebar from '@/components/sidebar';
import MetricCard from '@/components/metric-card';
import ComponentTable from '@/components/component-table';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function DashboardPage() {
  // Mock data - replace with real data from backend
  const metrics = [
    {
      title: 'Internal Risk',
      value: '2.3',
      description: 'Component quality score',
      color: 'orange' as const,
      href: '/internal-risk',
      status: 'warning' as const,
    },
    {
      title: 'Compatibility',
      value: '94%',
      description: 'Cross-component compatibility',
      color: 'blue' as const,
      href: '/compatibility',
      status: 'good' as const,
    },
    {
      title: 'Supplier Risk',
      value: '3.8',
      description: 'Supplier reliability score',
      color: 'red' as const,
      href: '/supplier-risk',
      status: 'critical' as const,
    },
  ];

  const components = [
    {
      id: '1',
      name: 'Microprocessor MCU-2024',
      supplier: 'TechCorp Industries',
      quantity: 150,
      status: 'warning',
      riskScore: 6.2,
    },
    {
      id: '2',
      name: 'Voltage Regulator VR-500',
      supplier: 'PowerTech Solutions',
      quantity: 300,
      status: 'good',
      riskScore: 2.1,
    },
    {
      id: '3',
      name: 'Capacitor Bank CB-1000',
      supplier: 'ElectroSupply Co',
      quantity: 500,
      status: 'critical',
      riskScore: 7.8,
    },
    {
      id: '4',
      name: 'Connector Module CN-PRO',
      supplier: 'ConnectTech Ltd',
      quantity: 250,
      status: 'good',
      riskScore: 1.9,
    },
  ];

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <main className="flex-1 overflow-auto">
        <div className="p-8 space-y-8">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
              <p className="text-foreground/60 mt-1">Supply chain analysis and component overview</p>
            </div>
            <Button className="bg-primary hover:bg-primary/90">
              Upload New Files
            </Button>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {metrics.map((metric) => (
              <MetricCard
                key={metric.title}
                title={metric.title}
                value={metric.value}
                description={metric.description}
                color={metric.color}
                href={metric.href}
                status={metric.status}
              />
            ))}
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle>Analysis Summary</CardTitle>
                <CardDescription>Latest analysis results</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-foreground/60">Total Components</span>
                  <span className="text-2xl font-bold text-foreground">1,200</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-foreground/60">Active Suppliers</span>
                  <span className="text-2xl font-bold text-foreground">48</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-foreground/60">Last Updated</span>
                  <span className="text-foreground">Today at 2:30 PM</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle>Risk Distribution</CardTitle>
                <CardDescription>Components by risk level</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-foreground/60">Low Risk</span>
                  <div className="flex items-center gap-2">
                    <div className="h-2 bg-green-500 rounded-full" style={{ width: '480px' }}></div>
                    <span className="text-foreground font-bold">40%</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-foreground/60">Medium Risk</span>
                  <div className="flex items-center gap-2">
                    <div className="h-2 bg-yellow-500 rounded-full" style={{ width: '360px' }}></div>
                    <span className="text-foreground font-bold">30%</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-foreground/60">High Risk</span>
                  <div className="flex items-center gap-2">
                    <div className="h-2 bg-red-500 rounded-full" style={{ width: '240px' }}></div>
                    <span className="text-foreground font-bold">30%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Components Table */}
          <div>
            <h2 className="text-xl font-bold text-foreground mb-4">Component Overview</h2>
            <ComponentTable components={components} />
          </div>
        </div>
      </main>
    </div>
  );
}
