import Sidebar from '@/components/sidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function CompatibilityPage() {
  const compatibilityMatrix = [
    { component: 'MCU-2024', voltage: '3.3V', current: '500mA', compatible: 15, incompatible: 2 },
    { component: 'VR-500', voltage: '5V', current: '2A', compatible: 28, incompatible: 1 },
    { component: 'CB-1000', voltage: 'Multi', current: '1A', compatible: 42, incompatible: 3 },
    { component: 'CN-PRO', voltage: '3.3V/5V', current: '100mA', compatible: 35, incompatible: 0 },
  ];

  const issues = [
    {
      title: 'Voltage Mismatch',
      count: 6,
      severity: 'medium',
      description: 'Components with incompatible voltage specifications',
    },
    {
      title: 'Current Limit Issues',
      count: 3,
      severity: 'high',
      description: 'Components exceeding current capacity limits',
    },
    {
      title: 'Pin Configuration',
      count: 2,
      severity: 'low',
      description: 'Minor pin arrangement incompatibilities',
    },
  ];

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <main className="flex-1 overflow-auto">
        <div className="p-8 space-y-8">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-foreground">Compatibility Analysis</h1>
            <p className="text-foreground/60 mt-1">Cross-component compatibility verification</p>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-500">94%</div>
                  <p className="text-sm text-foreground/60 mt-2">Compatibility Rate</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-500">1,120</div>
                  <p className="text-sm text-foreground/60 mt-2">Compatible Pairs</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-500">80</div>
                  <p className="text-sm text-foreground/60 mt-2">Incompatible Pairs</p>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-yellow-500">11</div>
                  <p className="text-sm text-foreground/60 mt-2">Critical Issues</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Compatibility Matrix */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle>Component Compatibility Matrix</CardTitle>
              <CardDescription>Compatibility overview for major components</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="px-4 py-3 text-left font-semibold text-foreground">Component</th>
                      <th className="px-4 py-3 text-left font-semibold text-foreground">Voltage</th>
                      <th className="px-4 py-3 text-left font-semibold text-foreground">Current</th>
                      <th className="px-4 py-3 text-center font-semibold text-foreground">Compatible</th>
                      <th className="px-4 py-3 text-center font-semibold text-foreground">Incompatible</th>
                      <th className="px-4 py-3 text-center font-semibold text-foreground">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compatibilityMatrix.map((row) => (
                      <tr key={row.component} className="border-b border-border hover:bg-muted/50">
                        <td className="px-4 py-3 font-medium text-foreground">{row.component}</td>
                        <td className="px-4 py-3 text-foreground/60">{row.voltage}</td>
                        <td className="px-4 py-3 text-foreground/60">{row.current}</td>
                        <td className="px-4 py-3 text-center">
                          <span className="text-green-500 font-bold">{row.compatible}</span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="text-red-500 font-bold">{row.incompatible}</span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          {row.incompatible === 0 ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/20 text-green-500 border border-green-500/30">
                              Verified
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-500/20 text-yellow-500 border border-yellow-500/30">
                              Review
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Issues */}
          <div>
            <h2 className="text-xl font-bold text-foreground mb-4">Compatibility Issues</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {issues.map((issue) => (
                <Card
                  key={issue.title}
                  className={`border-l-4 ${
                    issue.severity === 'high'
                      ? 'border-l-red-500 bg-red-500/5'
                      : issue.severity === 'medium'
                      ? 'border-l-yellow-500 bg-yellow-500/5'
                      : 'border-l-blue-500 bg-blue-500/5'
                  }`}
                >
                  <CardHeader>
                    <CardTitle className="text-lg">{issue.title}</CardTitle>
                    <CardDescription>{issue.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-foreground">{issue.count}</div>
                    <p className="text-xs text-foreground/60 mt-1">Issues found</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          <Card className="bg-card border-border border-l-4 border-l-blue-500">
            <CardHeader>
              <CardTitle className="text-lg">Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-foreground/80">
                <li className="flex items-start gap-3">
                  <span className="text-blue-500 font-bold mt-1">1</span>
                  <span>Resolve voltage mismatches by implementing voltage regulators or component replacements</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-500 font-bold mt-1">2</span>
                  <span>Upgrade power supply to handle maximum current requirements</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-blue-500 font-bold mt-1">3</span>
                  <span>Verify and update PCB layout to ensure proper pin connections</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
