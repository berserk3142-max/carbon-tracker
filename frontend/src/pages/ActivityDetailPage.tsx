import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { activitiesAPI, auditsAPI } from '@/lib/api';
import { useState } from 'react';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Lock,
  AlertTriangle,
  Clock,
  FileJson,
  History,
  Edit3,
  Save,
} from 'lucide-react';

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  validated: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  flagged: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  approved: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  rejected: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  locked: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
};

export default function ActivityDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [comment, setComment] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<Record<string, any>>({});
  const [activeTab, setActiveTab] = useState<'details' | 'raw' | 'audit'>('details');

  const { data: record, isLoading } = useQuery({
    queryKey: ['activity', id],
    queryFn: () => activitiesAPI.get(Number(id)).then((r) => r.data),
    enabled: !!id,
  });

  const { data: auditLogs } = useQuery({
    queryKey: ['audit-trail', id],
    queryFn: () => auditsAPI.getRecordTrail(Number(id)).then((r) => r.data),
    enabled: !!id,
  });

  const approveMut = useMutation({
    mutationFn: () => activitiesAPI.approve(Number(id), comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity', id] });
      queryClient.invalidateQueries({ queryKey: ['audit-trail', id] });
      queryClient.invalidateQueries({ queryKey: ['activities'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      setComment('');
    },
  });

  const rejectMut = useMutation({
    mutationFn: () => activitiesAPI.reject(Number(id), comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity', id] });
      queryClient.invalidateQueries({ queryKey: ['audit-trail', id] });
      queryClient.invalidateQueries({ queryKey: ['activities'] });
      setComment('');
    },
  });

  const lockMut = useMutation({
    mutationFn: () => activitiesAPI.lock(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity', id] });
      queryClient.invalidateQueries({ queryKey: ['audit-trail', id] });
      queryClient.invalidateQueries({ queryKey: ['activities'] });
    },
  });

  const editMut = useMutation({
    mutationFn: (data: Record<string, any>) => activitiesAPI.update(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity', id] });
      queryClient.invalidateQueries({ queryKey: ['audit-trail', id] });
      setIsEditing(false);
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-32 bg-muted rounded animate-pulse" />
        <div className="h-96 bg-muted rounded-xl animate-pulse" />
      </div>
    );
  }

  if (!record) {
    return <div className="text-center py-12 text-muted-foreground">Record not found</div>;
  }

  const startEdit = () => {
    setEditData({
      normalized_quantity: record.normalized_quantity,
      normalized_unit: record.normalized_unit,
      co2e_kg: record.co2e_kg,
      activity_type: record.activity_type,
      scope: record.scope,
      description: record.description,
    });
    setIsEditing(true);
  };

  return (
    <div className="space-y-7 max-w-6xl">
      {/* Header */}
      <div className="page-heading">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/review')}
            className="action-button p-2 rounded-md hover:bg-muted"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="page-title">{record.activity_type}</h1>
            <p className="text-sm text-muted-foreground">
              Record #{record.id}, {record.datasource_name || 'Unknown source'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_STYLES[record.status]}`}>
            {record.status}
          </span>
          {record.locked && (
            <span className="flex items-center gap-1 text-blue-600">
              <Lock className="w-4 h-4" />
            </span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="surface-panel flex gap-1 overflow-x-auto px-2">
        {[
          { key: 'details', label: 'Normalized Data', icon: Edit3 },
          { key: 'raw', label: 'Raw Source Data', icon: FileJson },
          { key: 'audit', label: 'Audit Trail', icon: History },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`tab-button flex items-center gap-2 px-4 py-3 text-sm font-medium ${
                activeTab === tab.key
                  ? 'tab-button-active'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {activeTab === 'details' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Validation Flags */}
            {record.suspicious && record.suspicious_reasons?.length > 0 && (
              <div className="surface-panel bg-amber-50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-800 p-4">
                <h3 className="font-semibold text-amber-800 dark:text-amber-400 flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-4 h-4" />
                  Validation Flags ({record.suspicious_reasons.length})
                </h3>
                <div className="space-y-2">
                  {record.suspicious_reasons.map((flag: any, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-sm">
                      <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                        flag.severity === 'error' ? 'bg-red-100 text-red-700' :
                        flag.severity === 'warning' ? 'bg-amber-100 text-amber-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {flag.severity}
                      </span>
                      <span className="text-amber-900 dark:text-amber-300">{flag.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Normalized Data */}
            <div className="surface-panel p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">Normalized Record</h3>
                {!record.locked && !isEditing && (
                  <button
                    onClick={startEdit}
                    className="action-button flex items-center gap-1 px-3 py-1.5 rounded-md text-sm border border-border hover:bg-muted"
                  >
                    <Edit3 className="w-3 h-3" />
                    Edit
                  </button>
                )}
                {isEditing && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => setIsEditing(false)}
                      className="action-button px-3 py-1.5 rounded-md text-sm border border-border hover:bg-muted"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => editMut.mutate(editData)}
                      disabled={editMut.isPending}
                      className="action-button flex items-center gap-1 px-3 py-1.5 rounded-md text-sm bg-primary text-primary-foreground hover:opacity-90"
                    >
                      <Save className="w-3 h-3" />
                      Save
                    </button>
                  </div>
                )}
              </div>

              <div className="detail-grid">
                {[
                  { label: 'Activity Type', key: 'activity_type', value: record.activity_type, editable: true },
                  { label: 'Scope', key: 'scope', value: `Scope ${record.scope}` },
                  { label: 'Category', key: 'category', value: record.category },
                  { label: 'Original Quantity', value: `${record.quantity} ${record.original_unit}` },
                  { label: 'Normalized Quantity', key: 'normalized_quantity', value: `${record.normalized_quantity}`, editable: true },
                  { label: 'Normalized Unit', key: 'normalized_unit', value: record.normalized_unit, editable: true },
                  { label: 'Emission Factor', value: record.emission_factor_value ? `${record.emission_factor_value} kg CO2e/${record.normalized_unit}` : 'Not found' },
                  { label: 'CO2e (kg)', key: 'co2e_kg', value: record.co2e_kg?.toFixed(2) || 'N/A', editable: true },
                  { label: 'Activity Date', value: record.activity_date || 'N/A' },
                  { label: 'Plant Code', value: record.plant_code || 'N/A' },
                  { label: 'Facility', value: record.facility || 'N/A' },
                  { label: 'Source File', value: record.datasource_name || 'N/A' },
                ].map((field) => (
                  <div key={field.label} className="detail-cell space-y-1">
                    <label className="text-xs text-muted-foreground">{field.label}</label>
                    {isEditing && field.editable && field.key ? (
                      <input
                        type={field.key === 'normalized_quantity' || field.key === 'co2e_kg' ? 'number' : 'text'}
                        value={editData[field.key] ?? ''}
                        onChange={(e) => setEditData({ ...editData, [field.key!]: e.target.value })}
                        className="control-field w-full px-2 py-1.5 text-sm"
                        step={field.key === 'normalized_quantity' || field.key === 'co2e_kg' ? '0.01' : undefined}
                      />
                    ) : (
                      <p className="text-sm font-medium">{field.value}</p>
                    )}
                  </div>
                ))}
              </div>

              {record.description && (
                <div className="mt-4 pt-4 border-t border-border">
                  <label className="text-xs text-muted-foreground">Description</label>
                  <p className="text-sm mt-1">{record.description}</p>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar review actions */}
          <div className="space-y-4">
            {/* Review Actions */}
            {!record.locked && (
              <div className="surface-panel p-4">
                <h3 className="font-semibold mb-3">Review Actions</h3>
                <textarea
                  placeholder="Add a review comment..."
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  className="control-field w-full px-3 py-2 text-sm resize-none h-20 mb-3"
                />
                <div className="space-y-2">
                  <button
                    onClick={() => approveMut.mutate()}
                    disabled={approveMut.isPending}
                    className="action-button w-full flex items-center justify-center gap-2 py-2 rounded-md bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Approve
                  </button>
                  <button
                    onClick={() => rejectMut.mutate()}
                    disabled={rejectMut.isPending}
                    className="action-button w-full flex items-center justify-center gap-2 py-2 rounded-md bg-red-600 text-white text-sm font-medium hover:bg-red-700 disabled:opacity-50"
                  >
                    <XCircle className="w-4 h-4" />
                    Reject
                  </button>
                  {record.status === 'approved' && (
                    <button
                      onClick={() => lockMut.mutate()}
                      disabled={lockMut.isPending}
                      className="action-button w-full flex items-center justify-center gap-2 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                    >
                      <Lock className="w-4 h-4" />
                      Lock for Audit
                    </button>
                  )}
                </div>
              </div>
            )}

            {record.locked && (
              <div className="surface-panel bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-800 p-4 text-center">
                <Lock className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                <p className="font-semibold text-blue-700 dark:text-blue-400">Locked for Audit</p>
                <p className="text-xs text-blue-600 dark:text-blue-300 mt-1">
                  Locked at {record.locked_at ? new Date(record.locked_at).toLocaleString() : 'N/A'}
                </p>
              </div>
            )}

            {/* Review Info */}
            {record.reviewed_by && (
              <div className="surface-panel p-4">
                <h3 className="text-xs text-muted-foreground mb-2">Reviewed By</h3>
                <p className="text-sm font-medium">{record.reviewed_by_name}</p>
                <p className="text-xs text-muted-foreground">
                  {record.reviewed_at ? new Date(record.reviewed_at).toLocaleString() : ''}
                </p>
                {record.reviewer_comment && (
                  <p className="text-sm mt-2 p-2 rounded-md bg-muted italic">
                    "{record.reviewer_comment}"
                  </p>
                )}
              </div>
            )}

            {/* Emission Factor */}
            {record.emission_factor_detail && (
              <div className="surface-panel p-4">
                <h3 className="text-xs text-muted-foreground mb-2">Emission Factor</h3>
                <p className="text-sm font-medium">
                  {record.emission_factor_detail.factor_value} {record.emission_factor_detail.factor_unit}
                  <span className="text-muted-foreground"> / {record.emission_factor_detail.unit}</span>
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Source: {record.emission_factor_detail.source}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'raw' && (
        <div className="surface-panel p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <FileJson className="w-4 h-4" />
            Raw Source Data (Immutable)
          </h3>
          {record.raw_record ? (
            <pre className="bg-muted rounded-md p-4 text-sm overflow-x-auto font-mono">
              {JSON.stringify(record.raw_record.raw_payload, null, 2)}
            </pre>
          ) : (
            <p className="text-muted-foreground text-sm">No raw record linked.</p>
          )}
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="surface-panel p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <History className="w-4 h-4" />
            Audit Trail
          </h3>
          {auditLogs && auditLogs.length > 0 ? (
            <div className="space-y-4">
              {auditLogs.map((log: any) => (
                <div key={log.id} className="flex gap-4 pb-4 border-b border-border/50 last:border-0">
                  <div className="flex flex-col items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs ${
                      log.action === 'approved' ? 'bg-emerald-500' :
                      log.action === 'rejected' ? 'bg-red-500' :
                      log.action === 'locked' ? 'bg-blue-500' :
                      'bg-gray-400'
                    }`}>
                      {log.action === 'approved' ? <CheckCircle2 className="w-4 h-4" /> :
                       log.action === 'rejected' ? <XCircle className="w-4 h-4" /> :
                       log.action === 'locked' ? <Lock className="w-4 h-4" /> :
                       <Clock className="w-4 h-4" />}
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm capitalize">{log.action}</span>
                      <span className="text-xs text-muted-foreground">
                        by {log.changed_by_name}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(log.timestamp).toLocaleString()}
                      </span>
                    </div>
                    {log.comment && (
                      <p className="text-sm text-muted-foreground mt-1 italic">"{log.comment}"</p>
                    )}
                    {log.old_values && Object.keys(log.old_values).length > 0 && (
                      <div className="mt-2 text-xs space-y-1">
                        {Object.entries(log.old_values).map(([key, oldVal]) => (
                          <div key={key} className="flex items-center gap-2">
                            <span className="text-muted-foreground">{key}:</span>
                            <span className="line-through text-red-500">{String(oldVal)}</span>
                            <span className="text-muted-foreground">→</span>
                            <span className="text-emerald-600">{String((log.new_values as any)?.[key])}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm py-4 text-center">
              No audit history yet.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
