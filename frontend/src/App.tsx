import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/auth';
import { lazy, Suspense, useEffect } from 'react';
import { authAPI } from '@/lib/api';
import Layout from '@/components/Layout';

const LoginPage = lazy(() => import('@/pages/LoginPage'));
const DashboardPage = lazy(() => import('@/pages/DashboardPage'));
const UploadsPage = lazy(() => import('@/pages/UploadsPage'));
const ReviewPage = lazy(() => import('@/pages/ReviewPage'));
const ActivityDetailPage = lazy(() => import('@/pages/ActivityDetailPage'));
const AuditLogPage = lazy(() => import('@/pages/AuditLogPage'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function PageFallback() {
  return (
    <div className="p-8">
      <div className="h-8 w-48 bg-muted rounded animate-pulse mb-6" />
      <div className="h-80 bg-muted rounded-xl animate-pulse" />
    </div>
  );
}

function AppContent() {
  const { isAuthenticated, setUser } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      authAPI.me().then((res) => setUser(res.data)).catch(() => {});
    }
  }, [isAuthenticated, setUser]);

  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/uploads" element={<UploadsPage />} />
                  <Route path="/review" element={<ReviewPage />} />
                  <Route path="/activity/:id" element={<ActivityDetailPage />} />
                  <Route path="/audit-log" element={<AuditLogPage />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Suspense>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
