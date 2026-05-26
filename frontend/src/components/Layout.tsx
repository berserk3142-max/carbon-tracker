import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth';
import {
  LayoutDashboard,
  Upload,
  ClipboardCheck,
  ScrollText,
  LogOut,
  Leaf,
  User,
} from 'lucide-react';
import type { ReactNode } from 'react';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/uploads', label: 'Upload Data', icon: Upload },
  { path: '/review', label: 'Review Queue', icon: ClipboardCheck },
  { path: '/audit-log', label: 'Audit Log', icon: ScrollText },
];

export default function Layout({ children }: { children: ReactNode }) {
  const location = useLocation();
  const { user, logout } = useAuthStore();

  return (
    <div className="app-frame flex h-screen">
      {/* Sidebar */}
      <aside className="sidebar-shell w-64 flex flex-col">
        {/* Logo */}
        <div className="p-5 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="brand-mark w-9 h-9 rounded-md flex items-center justify-center">
              <Leaf className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-none">CarbonTrack</h1>
              <p className="text-xs text-muted-foreground">ESG Data Platform</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1.5">
          {navItems.map((item) => {
            const isActive = location.pathname.startsWith(item.path);
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-link flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium ${
                  isActive
                    ? 'nav-link-active'
                    : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground'
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* User info */}
        <div className="p-3 border-t border-border">
          <div className="surface-panel p-3">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-md bg-primary/10 flex items-center justify-center">
              <User className="w-4 h-4 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {user?.first_name || user?.username || 'User'}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {user?.organization?.name || 'Organization'}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="action-button flex items-center gap-2 w-full px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="content-shell">{children}</div>
      </main>
    </div>
  );
}
