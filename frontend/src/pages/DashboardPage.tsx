import { useQuery } from '@tanstack/react-query';
import { activitiesAPI, ingestionAPI } from '@/lib/api';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Lock,
  TrendingUp,
  Upload,
  Flame,
  Zap,
  Plane,
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const SCOPE_COLORS = ['#10b981', '#3b82f6', '#8b5cf6'];
const SCOPE_LABELS = ['Scope 1', 'Scope 2', 'Scope 3'];
const SCOPE_ICONS = [Flame, Zap, Plane];

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => activitiesAPI.stats().then((r) => r.data),
  });

  const { data: sources } = useQuery({
    queryKey: ['recent-uploads'],
    queryFn: () => ingestionAPI.getSources().then((r) => r.data.results || r.data),
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 w-48 bg-muted rounded mb-6" />
          <div className="grid grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-28 bg-muted rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  const scopeData = [
    { name: 'Scope 1', value: stats?.scope_1_co2e || 0, label: 'Direct Emissions' },
    { name: 'Scope 2', value: stats?.scope_2_co2e || 0, label: 'Electricity' },
    { name: 'Scope 3', value: stats?.scope_3_co2e || 0, label: 'Travel & Others' },
  ].filter((d) => d.value > 0);

  const statusData = [
    { name: 'Pending', value: stats?.pending_review || 0, color: '#f59e0b' },
    { name: 'Flagged', value: stats?.flagged || 0, color: '#ef4444' },
    { name: 'Approved', value: stats?.approved || 0, color: '#10b981' },
    { name: 'Locked', value: stats?.locked || 0, color: '#3b82f6' },
  ];

  const formatCO2 = (kg: number) => {
    if (kg >= 1000) return `${(kg / 1000).toFixed(1)}t`;
    return `${kg.toFixed(0)}kg`;
  };

  const statCards = [
    { label: 'Total Records', value: stats?.total_records || 0, icon: Activity, color: 'text-primary' },
    { label: 'Pending Review', value: stats?.pending_review || 0, icon: AlertTriangle, color: 'text-amber-500' },
    { label: 'Flagged', value: stats?.flagged || 0, icon: AlertTriangle, color: 'text-red-500' },
    { label: 'Approved', value: stats?.approved || 0, icon: CheckCircle2, color: 'text-emerald-500' },
    { label: 'Locked', value: stats?.locked || 0, icon: Lock, color: 'text-blue-500' },
    { label: 'Total CO2e', value: formatCO2(stats?.total_co2e_kg || 0), icon: TrendingUp, color: 'text-primary' },
  ];

  return (
    <div className="space-y-7">
      <div className="page-heading">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">
          Carbon emissions overview and data quality metrics
          </p>
        </div>
        <div className="hidden md:flex items-center gap-2 rounded-md border border-border bg-card px-3 py-2 text-xs text-muted-foreground shadow-sm">
          <span className="h-2 w-2 rounded-full bg-primary" />
          Live workspace
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.label}
              className="surface-panel metric-card"
            >
              <div className="flex items-center justify-between gap-2 mb-4">
                <span className="text-xs font-medium text-muted-foreground">{card.label}</span>
                <span className="metric-icon">
                  <Icon className={`w-4 h-4 ${card.color}`} />
                </span>
              </div>
              <p className="text-2xl font-bold tracking-tight">{card.value}</p>
            </div>
          );
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scope Breakdown */}
        <div className="surface-panel p-6">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-semibold">Emissions by Scope</h3>
            <span className="text-xs text-muted-foreground">CO2e split</span>
          </div>
          {scopeData.length > 0 ? (
            <div className="flex flex-col sm:flex-row sm:items-center gap-6 lg:gap-8">
              <div className="w-48 h-48 shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={scopeData}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={80}
                      dataKey="value"
                      stroke="none"
                    >
                      {scopeData.map((_, idx) => (
                        <Cell key={idx} fill={SCOPE_COLORS[idx]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value) => [`${formatCO2(Number(value ?? 0))} CO2e`, '']}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-3">
                {scopeData.map((d, idx) => {
                  const Icon = SCOPE_ICONS[idx];
                  return (
                    <div key={d.name} className="flex items-center gap-3 rounded-md px-2 py-1.5 hover:bg-muted/50 transition-colors">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: SCOPE_COLORS[idx] }}
                      />
                      <Icon className="w-4 h-4 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium">{d.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatCO2(d.value)} CO2e, {d.label}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground text-sm py-8 text-center">
              No emission data yet. Upload data to get started.
            </p>
          )}
        </div>

        {/* Record Status */}
        <div className="surface-panel p-6">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-semibold">Record Status Distribution</h3>
            <span className="text-xs text-muted-foreground">Review flow</span>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={statusData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {statusData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Uploads */}
      <div className="surface-panel p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Recent Uploads</h3>
          <a
            href="/uploads"
            className="action-button text-sm text-primary hover:bg-primary/10 flex items-center gap-1 px-2 py-1 rounded-md"
          >
            <Upload className="w-3 h-3" />
            Upload New
          </a>
        </div>
        {sources && sources.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="data-table w-full text-sm">
              <thead>
                <tr>
                  <th className="text-left py-2 px-3 text-muted-foreground font-medium">File</th>
                  <th className="text-left py-2 px-3 text-muted-foreground font-medium">Source</th>
                  <th className="text-left py-2 px-3 text-muted-foreground font-medium">Status</th>
                  <th className="text-left py-2 px-3 text-muted-foreground font-medium">Rows</th>
                  <th className="text-left py-2 px-3 text-muted-foreground font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {sources.slice(0, 5).map((s: any) => (
                  <tr key={s.id} className="border-b border-border/50">
                    <td className="py-2 px-3 font-medium">{s.file_name}</td>
                    <td className="py-2 px-3">
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                        {s.source_type.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2 px-3">
                      <StatusBadge status={s.status} />
                    </td>
                    <td className="py-2 px-3 text-muted-foreground">
                      {s.processed_rows}/{s.total_rows}
                    </td>
                    <td className="py-2 px-3 text-muted-foreground">
                      {new Date(s.uploaded_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-muted-foreground text-sm py-4 text-center">
            No uploads yet. Start by uploading SAP, Utility, or Travel CSV data.
          </p>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
    failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    partial: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    parsing: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    normalizing: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    uploading: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
  };

  return (
    <span
      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
        styles[status] || styles.uploading
      }`}
    >
      {status}
    </span>
  );
}
