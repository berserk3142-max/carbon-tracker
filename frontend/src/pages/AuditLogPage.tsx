import { useQuery } from '@tanstack/react-query';
import { auditsAPI } from '@/lib/api';
import {
  CheckCircle2,
  XCircle,
  Lock,
  Clock,
  Edit3,
  History,
  MessageSquare,
} from 'lucide-react';

const ACTION_CONFIG: Record<string, { icon: any; color: string; bg: string }> = {
  created: { icon: Clock, color: 'text-gray-600', bg: 'bg-gray-100 dark:bg-gray-800' },
  updated: { icon: Edit3, color: 'text-blue-600', bg: 'bg-blue-100 dark:bg-blue-900/30' },
  approved: { icon: CheckCircle2, color: 'text-emerald-600', bg: 'bg-emerald-100 dark:bg-emerald-900/30' },
  rejected: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-100 dark:bg-red-900/30' },
  locked: { icon: Lock, color: 'text-blue-600', bg: 'bg-blue-100 dark:bg-blue-900/30' },
  unlocked: { icon: Lock, color: 'text-amber-600', bg: 'bg-amber-100 dark:bg-amber-900/30' },
  comment: { icon: MessageSquare, color: 'text-purple-600', bg: 'bg-purple-100 dark:bg-purple-900/30' },
};

export default function AuditLogPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: () => auditsAPI.list().then((r) => r.data.results || r.data),
  });

  return (
    <div className="space-y-7">
      <div className="page-heading">
        <div>
          <h1 className="page-title">Audit Log</h1>
          <p className="page-subtitle">
          Complete audit trail of all data changes, immutable and traceable
        </p>
        </div>
      </div>

      <div className="surface-panel overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-16 bg-muted rounded animate-pulse" />
            ))}
          </div>
        ) : data && data.length > 0 ? (
          <div className="divide-y divide-border">
            {data.map((log: any) => {
              const config = ACTION_CONFIG[log.action] || ACTION_CONFIG.created;
              const Icon = config.icon;
              return (
                <div
                  key={log.id}
                  className="flex items-start gap-4 p-4 hover:bg-muted/30 transition-colors"
                >
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${config.bg}`}>
                    <Icon className={`w-4 h-4 ${config.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm capitalize">{log.action}</span>
                      <span className="text-muted-foreground text-sm">on</span>
                      <a
                        href={`/activity/${log.record}`}
                        className="action-button text-sm text-primary hover:bg-primary/10 font-medium px-1 rounded-md"
                      >
                        Record #{log.record}
                      </a>
                      <span className="text-muted-foreground text-sm">by</span>
                      <span className="text-sm font-medium">{log.changed_by_name}</span>
                    </div>

                    {log.comment && (
                      <p className="text-sm text-muted-foreground mt-1 italic">
                        "{log.comment}"
                      </p>
                    )}

                    {log.old_values && Object.keys(log.old_values).length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {Object.entries(log.old_values).map(([key, oldVal]) => (
                          <span key={key} className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-muted text-xs">
                            <span className="font-medium">{key}:</span>
                            <span className="line-through text-red-500">{String(oldVal)}</span>
                            <span>→</span>
                            <span className="text-emerald-600">
                              {String((log.new_values as any)?.[key])}
                            </span>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground whitespace-nowrap flex-shrink-0">
                    {new Date(log.timestamp).toLocaleString()}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-12 text-center">
            <History className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">No audit logs yet.</p>
            <p className="text-sm text-muted-foreground mt-1">
              Audit logs are created automatically when records are reviewed, edited, or locked.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
