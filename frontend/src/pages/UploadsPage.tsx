import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ingestionAPI } from '@/lib/api';
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Factory,
  Zap,
  Plane,
} from 'lucide-react';

const SOURCE_TYPES = [
  {
    value: 'sap',
    label: 'SAP Fuel & Procurement',
    description: 'German SAP CSV exports (WERKS, MATNR, MENGE, MEINS, BUDAT)',
    icon: Factory,
  },
  {
    value: 'utility',
    label: 'Utility Electricity',
    description: 'Electricity billing CSVs with meter IDs and usage (kWh/MWh)',
    icon: Zap,
  },
  {
    value: 'travel',
    label: 'Travel & Expenses',
    description: 'Concur/Navan-style travel expense exports (flights, hotels, trains)',
    icon: Plane,
  },
];

export default function UploadsPage() {
  const queryClient = useQueryClient();
  const [selectedSource, setSelectedSource] = useState('sap');
  const [dragActive, setDragActive] = useState(false);

  const { data: sources, isLoading } = useQuery({
    queryKey: ['data-sources'],
    queryFn: () => ingestionAPI.getSources().then((r) => r.data.results || r.data),
  });

  const uploadMutation = useMutation({
    mutationFn: ({ file, sourceType }: { file: File; sourceType: string }) =>
      ingestionAPI.upload(file, sourceType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-sources'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files[0];
      if (file && file.name.endsWith('.csv')) {
        uploadMutation.mutate({ file, sourceType: selectedSource });
      }
    },
    [selectedSource, uploadMutation]
  );

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadMutation.mutate({ file, sourceType: selectedSource });
    }
    e.target.value = '';
  };

  return (
    <div className="space-y-7">
      <div className="page-heading">
        <div>
          <h1 className="page-title">Upload Data</h1>
          <p className="page-subtitle">
          Ingest CSV data from SAP, Utility, or Travel systems
          </p>
        </div>
      </div>

      {/* Source Type Selector */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {SOURCE_TYPES.map((st) => {
          const Icon = st.icon;
          return (
            <button
              key={st.value}
              onClick={() => setSelectedSource(st.value)}
              className={`source-tile p-4 text-left ${
                selectedSource === st.value ? 'source-tile-active' : ''
              }`}
            >
              <span className="metric-icon mb-3">
                <Icon className="w-4 h-4 text-primary" />
              </span>
              <h3 className="font-semibold">{st.label}</h3>
              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{st.description}</p>
            </button>
          );
        })}
      </div>

      {/* Upload Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`upload-zone border-2 border-dashed p-12 text-center transition-colors ${
          dragActive
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50'
        } ${uploadMutation.isPending ? 'opacity-50 pointer-events-none' : ''}`}
      >
        <Upload
          className={`w-10 h-10 mx-auto mb-4 ${
            dragActive ? 'text-primary' : 'text-muted-foreground'
          }`}
        />
        <p className="font-medium">
          {uploadMutation.isPending
            ? 'Processing...'
            : 'Drag & drop your CSV file here'}
        </p>
        <p className="text-sm text-muted-foreground mt-1">or click to browse</p>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileSelect}
          className="hidden"
          id="file-upload"
          disabled={uploadMutation.isPending}
        />
        <label
          htmlFor="file-upload"
          className="action-button inline-block mt-4 px-6 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium cursor-pointer hover:opacity-90"
        >
          Select File
        </label>

        {uploadMutation.isPending && (
          <div className="mt-4">
            <div className="w-48 h-1.5 bg-muted rounded-full mx-auto overflow-hidden">
              <div className="h-full bg-primary rounded-full animate-pulse w-3/4" />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Parsing, normalizing, and validating...
            </p>
          </div>
        )}

        {uploadMutation.isSuccess && (
          <div className="mt-4 p-3 rounded-lg bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 text-sm">
            <CheckCircle2 className="w-4 h-4 inline mr-1" />
            Upload processed successfully!{' '}
            {uploadMutation.data?.data?.results && (
              <span>
                {uploadMutation.data.data.results.processed} records processed,{' '}
                {uploadMutation.data.data.results.flagged} flagged.
              </span>
            )}
          </div>
        )}

        {uploadMutation.isError && (
          <div className="mt-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm">
            <XCircle className="w-4 h-4 inline mr-1" />
            Upload failed: {(uploadMutation.error as any)?.response?.data?.detail || 'Unknown error'}
          </div>
        )}
      </div>

      {/* Upload History */}
      <div className="surface-panel p-6">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4" />
          Upload History
        </h3>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-muted rounded animate-pulse" />
            ))}
          </div>
        ) : sources && sources.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="data-table w-full text-sm">
              <thead>
                <tr>
                  <th className="text-left py-3 px-3 text-muted-foreground font-medium">File Name</th>
                  <th className="text-left py-3 px-3 text-muted-foreground font-medium">Source Type</th>
                  <th className="text-left py-3 px-3 text-muted-foreground font-medium">Status</th>
                  <th className="text-left py-3 px-3 text-muted-foreground font-medium">Total Rows</th>
                  <th className="text-left py-3 px-3 text-muted-foreground font-medium">Processed</th>
                  <th className="text-left py-3 px-3 text-muted-foreground font-medium">Failed</th>
                  <th className="text-left py-3 px-3 text-muted-foreground font-medium">Uploaded By</th>
                  <th className="text-left py-3 px-3 text-muted-foreground font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((s: any) => (
                  <tr key={s.id} className="border-b border-border/50">
                    <td className="py-3 px-3 font-medium">{s.file_name}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                        {s.source_type.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <UploadStatusBadge status={s.status} />
                    </td>
                    <td className="py-3 px-3">{s.total_rows}</td>
                    <td className="py-3 px-3 text-emerald-600">{s.processed_rows}</td>
                    <td className="py-3 px-3 text-red-500">{s.failed_rows}</td>
                    <td className="py-3 px-3 text-muted-foreground">{s.uploaded_by_name}</td>
                    <td className="py-3 px-3 text-muted-foreground">
                      {new Date(s.uploaded_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-muted-foreground text-sm py-8 text-center">
            No files uploaded yet. Use the upload area above to get started.
          </p>
        )}
      </div>
    </div>
  );
}

function UploadStatusBadge({ status }: { status: string }) {
  const config: Record<string, { icon: any; className: string }> = {
    completed: { icon: CheckCircle2, className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
    failed: { icon: XCircle, className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
    partial: { icon: AlertTriangle, className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
    parsing: { icon: Clock, className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
    normalizing: { icon: Clock, className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
    uploading: { icon: Clock, className: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400' },
  };
  const c = config[status] || config.uploading;
  const Icon = c.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${c.className}`}>
      <Icon className="w-3 h-3" />
      {status}
    </span>
  );
}
