import { Card, CardContent } from '@/components/ui/card';

interface Component {
  id: string;
  name: string;
  supplier: string;
  quantity: number;
  status: 'good' | 'warning' | 'critical';
  riskScore: number;
}

interface ComponentTableProps {
  components: Component[];
}

const statusStyles = {
  good: {
    badge: 'bg-green-500/20 text-green-500 border-green-500/30',
    label: 'Good',
  },
  warning: {
    badge: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
    label: 'Warning',
  },
  critical: {
    badge: 'bg-red-500/20 text-red-500 border-red-500/30',
    label: 'Critical',
  },
};

export default function ComponentTable({ components }: ComponentTableProps) {
  return (
    <Card className="bg-card border-border">
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="px-6 py-4 text-left text-sm font-semibold text-foreground/80">Component Name</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-foreground/80">Supplier</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-foreground/80">Quantity</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-foreground/80">Status</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-foreground/80">Risk Score</th>
              </tr>
            </thead>
            <tbody>
              {components.map((component) => {
                const statusStyle = statusStyles[component.status];
                return (
                  <tr key={component.id} className="border-b border-border hover:bg-muted/50 transition-colors">
                    <td className="px-6 py-4">
                      <span className="text-sm font-medium text-foreground">{component.name}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-foreground/60">{component.supplier}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-foreground">{component.quantity}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${statusStyle.badge}`}>
                        {statusStyle.label}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              component.riskScore < 3
                                ? 'bg-green-500'
                                : component.riskScore < 6
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                            style={{ width: `${(component.riskScore / 10) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-foreground min-w-fit">{component.riskScore.toFixed(1)}</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
