import Sidebar from '@/components/sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import ComponentTable from '@/components/component-table';

export default function InternalRiskPage() {
  const components = [
    {
      id: '1',
      name: 'Microprocessor MCU-2024',
      supplier: 'TechCorp Industries',
      quantity: 150,
      status: 'warning' as const,
      riskScore: 6.2,
    },
    {
      id: '2',
      name: 'Voltage Regulator VR-500',
      supplier: 'PowerTech Solutions',
      quantity: 300,
      status: 'good' as const,
      riskScore: 2.1,
    },
    {
      id: '3',
      name: 'Capacitor Bank CB-1000',
      supplier: 'ElectroSupply Co',
      quantity: 500,
      status: 'critical' as const,
      riskScore: 7.8,
    },
    {
      id: '4',
      name: 'Connector Module CN-PRO',
      supplier: 'ConnectTech Ltd',
      quantity: 250,
      status: 'good' as const,
      riskScore: 1.9,
    },
  ];

  const riskFactors = [
    { factor: 'Component Degradation', impact: 35, color: 'bg-orange-500' },
    { factor: 'Manufacturing Tolerance', impact: 25, color: 'bg-blue-500' },
    { factor: 'Environmental Sensitivity', impact: 20, color: 'bg-yellow-500' },
    { factor: 'Lifecycle Management', impact: 20, color: 'bg-red-500' },
  ];

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <main className="flex-1 overflow-auto">
        <div className="p-8 space-y-8">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-foreground">Internal Risk Analysis</h1>
            <p className="text-foreground/60 mt-1">Component quality and performance metrics</p>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-500">2.3</div>
                  <p className="text-sm text-foreground/60 mt-2">Average Risk Score</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-500">850</div>
                  <p className="text-sm text-foreground/60 mt-2">Low Risk Components</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-yellow-500">270</div>
                  <p className="text-sm text-foreground/60 mt-2">Medium Risk Components</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-500">80</div>
                  <p className="text-sm text-foreground/60 mt-2">High Risk Components</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Risk Factors */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle>Risk Factor Breakdown</CardTitle>
              <CardDescription>Contributing factors to internal risk score</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {riskFactors.map((item) => (
                <div key={item.factor} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-foreground font-medium">{item.factor}</span>
                    <span className="text-foreground/60">{item.impact}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${item.color}`}
                      style={{ width: `${item.impact}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Component Details */}
          <div>
            <h2 className="text-xl font-bold text-foreground mb-4">Components by Risk</h2>
            <ComponentTable components={components} />
          </div>

          {/* Recommendations */}
          <Card className="bg-card border-border border-l-4 border-l-orange-500">
            <CardHeader>
              <CardTitle className="text-lg">Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-foreground/80">
                <li className="flex items-start gap-3">
                  <span className="text-orange-500 font-bold mt-1">1</span>
                  <span>Review and update component specifications for MCU-2024 to address degradation risks</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-orange-500 font-bold mt-1">2</span>
                  <span>Implement stricter quality control for capacitor bank components</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-orange-500 font-bold mt-1">3</span>
                  <span>Consider alternative suppliers for high-risk components</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
