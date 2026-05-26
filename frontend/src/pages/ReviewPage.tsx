import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { activitiesAPI } from '@/lib/api';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Lock,
  Eye,
  Filter,
  ChevronDown,
} from 'lucide-react';

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'validated', label: 'Validated' },
  { value: 'flagged', label: 'Flagged' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'locked', label: 'Locked' },
];

const SCOPE_OPTIONS = [
  { value: '', label: 'All Scopes' },
  { value: '1', label: 'Scope 1' },
  { value: '2', label: 'Scope 2' },
  { value: '3', label: 'Scope 3' },
];

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  validated: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  flagged: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  approved: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  rejected: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  locked: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
};

const SCOPE_STYLES: Record<number, string> = {
  1: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  2: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400',
  3: 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400',
};

export default function ReviewPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({
    status: '',
    scope: '',
    suspicious: '',
    page: '1',
  });
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [bulkComment, setBulkComment] = useState('');

  const queryParams: Record<string, string> = { page: filters.page };
  if (filters.status) queryParams.status = filters.status;
  if (filters.scope) queryParams.scope = filters.scope;
  if (filters.suspicious) queryParams.suspicious = filters.suspicious;

  const { data, isLoading } = useQuery({
    queryKey: ['activities', queryParams],
    queryFn: () => activitiesAPI.list(queryParams).then((r) => r.data),
  });

  const records = data?.results || data || [];
  const totalCount = data?.count || records.length;

  const bulkApproveMut = useMutation({
    mutationFn: ({ ids, comment }: { ids: number[]; comment: string }) =>
      activitiesAPI.bulkApprove(ids, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activities'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      setSelectedIds([]);
    },
  });

  const bulkLockMut = useMutation({
    mutationFn: (ids: number[]) => activitiesAPI.bulkLock(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activities'] });
      setSelectedIds([]);
    },
  });

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const toggleAll = () => {
    if (selectedIds.length === records.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(records.map((r: any) => r.id));
    }
  };

  return (
    <div className="space-y-7">
      <div className="page-heading">
        <div>
          <h1 className="page-title">Review Queue</h1>
          <p className="page-subtitle">
            {totalCount} records, review, approve, or flag activity records
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="toolbar-surface flex items-center gap-3 flex-wrap">
        <Filter className="w-4 h-4 text-muted-foreground" />
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value, page: '1' })}
          className="control-field px-3 py-1.5 text-sm"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <select
          value={filters.scope}
          onChange={(e) => setFilters({ ...filters, scope: e.target.value, page: '1' })}
          className="control-field px-3 py-1.5 text-sm"
        >
          {SCOPE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={filters.suspicious === 'true'}
            onChange={(e) =>
              setFilters({
                ...filters,
                suspicious: e.target.checked ? 'true' : '',
                page: '1',
              })
            }
            className="rounded"
          />
          Suspicious Only
        </label>

        {/* Quick Filters */}
        <button
          onClick={() => setFilters({ status: 'flagged', scope: '', suspicious: '', page: '1' })}
          className="action-button px-3 py-1.5 rounded-md border border-red-200 bg-red-50 text-red-700 text-xs font-medium hover:bg-red-100 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400"
        >
          <AlertTriangle className="w-3 h-3 inline mr-1" />
          Flagged
        </button>
        <button
          onClick={() => setFilters({ status: '', scope: '', suspicious: '', page: '1' })}
          className="action-button px-3 py-1.5 rounded-md border border-border text-xs font-medium hover:bg-muted"
        >
          Clear Filters
        </button>
      </div>

      {/* Bulk Actions */}
      {selectedIds.length > 0 && (
        <div className="toolbar-surface flex items-center gap-3 flex-wrap bg-primary/5 border-primary/20">
          <span className="text-sm font-medium">
            {selectedIds.length} selected
          </span>
          <input
            type="text"
            placeholder="Optional comment..."
            value={bulkComment}
            onChange={(e) => setBulkComment(e.target.value)}
            className="control-field flex-1 px-3 py-1.5 text-sm max-w-xs"
          />
          <button
            onClick={() => bulkApproveMut.mutate({ ids: selectedIds, comment: bulkComment })}
            disabled={bulkApproveMut.isPending}
            className="action-button px-3 py-1.5 rounded-md bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
          >
            <CheckCircle2 className="w-3 h-3 inline mr-1" />
            Approve Selected
          </button>
          <button
            onClick={() => bulkLockMut.mutate(selectedIds)}
            disabled={bulkLockMut.isPending}
            className="action-button px-3 py-1.5 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            <Lock className="w-3 h-3 inline mr-1" />
            Lock Selected
          </button>
        </div>
      )}

      {/* Records Table */}
      <div className="surface-panel overflow-hidden">
        {isLoading ? (
          <div className="p-8 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 bg-muted rounded animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table w-full text-sm">
              <thead>
                <tr>
                  <th className="py-3 px-3 text-left">
                    <input
                      type="checkbox"
                      checked={selectedIds.length === records.length && records.length > 0}
                      onChange={toggleAll}
                      className="rounded"
                    />
                  </th>
                  <th className="py-3 px-3 text-left text-muted-foreground font-medium">Activity</th>
                  <th className="py-3 px-3 text-left text-muted-foreground font-medium">Scope</th>
                  <th className="py-3 px-3 text-left text-muted-foreground font-medium">Quantity</th>
                  <th className="py-3 px-3 text-left text-muted-foreground font-medium">Unit</th>
                  <th className="py-3 px-3 text-left text-muted-foreground font-medium">CO2e (kg)</th>
                  <th className="py-3 px-3 text-left text-muted-foreground font-medium">Date</th>
                  <th className="py-3 px-3 text-left text-muted-foreground font-medium">Status</th>
                  <th className="py-3 px-3 text-left text-muted-foreground font-medium">Flags</th>
                  <th className="py-3 px-3 text-left text-muted-foreground font-medium">Source</th>
                  <th className="py-3 px-3 text-left text-muted-foreground font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r: any) => (
                  <tr
                    key={r.id}
                    className={`border-b border-border/50 cursor-pointer ${
                      r.suspicious ? 'bg-red-50/30 dark:bg-red-900/5' : ''
                    }`}
                    onClick={() => navigate(`/activity/${r.id}`)}
                  >
                    <td className="py-3 px-3" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(r.id)}
                        onChange={() => toggleSelect(r.id)}
                        className="rounded"
                      />
                    </td>
                    <td className="py-3 px-3 font-medium max-w-[200px] truncate">
                      {r.activity_type}
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${SCOPE_STYLES[r.scope]}`}>
                        Scope {r.scope}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono">
                      {r.normalized_quantity?.toFixed(1)}
                    </td>
                    <td className="py-3 px-3 text-muted-foreground">
                      {r.normalized_unit}
                    </td>
                    <td className="py-3 px-3 font-mono">
                      {r.co2e_kg ? r.co2e_kg.toFixed(1) : 'N/A'}
                    </td>
                    <td className="py-3 px-3 text-muted-foreground">
                      {r.activity_date || 'N/A'}
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[r.status]}`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      {r.suspicious && r.suspicious_reasons?.length > 0 && (
                        <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                          <AlertTriangle className="w-3 h-3" />
                          <span className="text-xs">{r.suspicious_reasons.length}</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-muted-foreground text-xs truncate max-w-[120px]">
                      {r.datasource_name || 'N/A'}
                    </td>
                    <td className="py-3 px-3" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => navigate(`/activity/${r.id}`)}
                        className="action-button p-1.5 rounded-md hover:bg-muted"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {data?.count > 50 && (
          <div className="flex items-center justify-between p-4 border-t border-border">
            <span className="text-sm text-muted-foreground">
              Page {filters.page} of {Math.ceil(data.count / 50)}
            </span>
            <div className="flex gap-2">
              <button
                disabled={!data?.previous}
                onClick={() => setFilters({ ...filters, page: String(Number(filters.page) - 1) })}
                className="action-button px-3 py-1.5 rounded-md border border-border text-sm disabled:opacity-50 hover:bg-muted"
              >
                Previous
              </button>
              <button
                disabled={!data?.next}
                onClick={() => setFilters({ ...filters, page: String(Number(filters.page) + 1) })}
                className="action-button px-3 py-1.5 rounded-md border border-border text-sm disabled:opacity-50 hover:bg-muted"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
