import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth';
import { authAPI } from '@/lib/api';
import { Leaf } from 'lucide-react';

export default function LoginPage() {
  const navigate = useNavigate();
  const { setUser, setTokens } = useAuthStore();
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState({
    username: '',
    password: '',
    email: '',
    first_name: '',
    last_name: '',
    organization_name: '',
    industry: 'manufacturing',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let res;
      if (isRegister) {
        res = await authAPI.register(form);
      } else {
        res = await authAPI.login({
          username: form.username,
          password: form.password,
        });
      }

      setTokens(res.data.tokens.access, res.data.tokens.refresh);
      setUser(res.data.user);
      navigate('/dashboard');
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.non_field_errors?.[0] ||
        Object.values(err.response?.data || {}).flat().join(', ') ||
        'Something went wrong';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md p-8">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="brand-mark w-14 h-14 rounded-md flex items-center justify-center mb-4">
            <Leaf className="w-8 h-8 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">CarbonTrack</h1>
          <p className="text-muted-foreground mt-1">ESG Carbon Accounting Platform</p>
        </div>

        {/* Card */}
        <div className="surface-panel p-6">
          <h2 className="text-lg font-semibold mb-4">
            {isRegister ? 'Create Account' : 'Sign In'}
          </h2>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">Username</label>
              <input
                type="text"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                className="control-field w-full px-3 py-2 text-sm"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">Password</label>
              <input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="control-field w-full px-3 py-2 text-sm"
                required
              />
            </div>

            {isRegister && (
              <>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Email</label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="control-field w-full px-3 py-2 text-sm"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium mb-1.5">First Name</label>
                    <input
                      type="text"
                      value={form.first_name}
                      onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                      className="control-field w-full px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Last Name</label>
                    <input
                      type="text"
                      value={form.last_name}
                      onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                      className="control-field w-full px-3 py-2 text-sm"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Organization Name</label>
                  <input
                    type="text"
                    value={form.organization_name}
                    onChange={(e) => setForm({ ...form, organization_name: e.target.value })}
                    className="control-field w-full px-3 py-2 text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Industry</label>
                  <select
                    value={form.industry}
                    onChange={(e) => setForm({ ...form, industry: e.target.value })}
                    className="control-field w-full px-3 py-2 text-sm"
                  >
                    <option value="manufacturing">Manufacturing</option>
                    <option value="energy">Energy & Utilities</option>
                    <option value="logistics">Logistics & Transportation</option>
                    <option value="technology">Technology</option>
                    <option value="finance">Financial Services</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={loading}
              className="action-button w-full py-2.5 rounded-md bg-primary text-primary-foreground font-medium text-sm hover:opacity-90 disabled:opacity-50"
            >
              {loading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
            </button>
          </form>

          <div className="mt-4 text-center">
            <button
              onClick={() => {
                setIsRegister(!isRegister);
                setError('');
              }}
              className="action-button text-sm text-primary hover:bg-primary/10 px-2 py-1 rounded-md"
            >
              {isRegister
                ? 'Already have an account? Sign in'
                : "Don't have an account? Register"}
            </button>
          </div>

          {!isRegister && (
            <div className="mt-4 p-3 rounded-md bg-muted text-xs text-muted-foreground">
              <p className="font-medium mb-1">Demo Credentials:</p>
              <p>Admin: admin / admin123</p>
              <p>Analyst: analyst / analyst123</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
