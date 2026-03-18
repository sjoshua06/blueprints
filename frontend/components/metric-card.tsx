import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface MetricCardProps {
  title: string;
  value: string | number;
  description: string;
  color: 'orange' | 'blue' | 'red';
  href: string;
  status: 'good' | 'warning' | 'critical';
}

const colorClasses = {
  orange: {
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    text: 'text-orange-500',
    button: 'bg-orange-500 hover:bg-orange-600 text-white',
  },
  blue: {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    text: 'text-blue-500',
    button: 'bg-blue-500 hover:bg-blue-600 text-white',
  },
  red: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    text: 'text-red-500',
    button: 'bg-red-500 hover:bg-red-600 text-white',
  },
};

const statusEmoji = {
  good: '✓',
  warning: '⚠',
  critical: '✕',
};

export default function MetricCard({
  title,
  value,
  description,
  color,
  href,
  status,
}: MetricCardProps) {
  const colors = colorClasses[color];

  return (
    <Card className={`border-2 ${colors.border} ${colors.bg}`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            <CardDescription className="mt-1">{description}</CardDescription>
          </div>
          <div className={`text-2xl font-bold ${colors.text}`}>
            {statusEmoji[status]}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          <div className={`text-4xl font-bold ${colors.text}`}>{value}</div>
          
          <Link href={href}>
            <Button className={`w-full ${colors.button}`}>
              View Details →
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
