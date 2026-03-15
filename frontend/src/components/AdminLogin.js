import { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Mail, Lock, ArrowRight, Loader2, Shield } from 'lucide-react';
import api from '@/api';

export default function AdminLogin({ onBack, onAdminAuth }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) return;
    setLoading(true); setError('');
    try {
      const res = await api.adminLogin({ email: email.trim(), password });
      localStorage.setItem('wtf_admin_token', res.token);
      onAdminAuth();
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid admin credentials');
    } finally { setLoading(false); }
  };

  return (
    <div data-testid="admin-login" className="min-h-screen flex items-center justify-center px-5 py-10">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm">
        <button data-testid="admin-back" onClick={onBack}
          className="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center mb-6 hover:bg-gray-200 transition-colors">
          <ArrowLeft size={18} className="text-gray-600" />
        </button>

        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gray-900 text-white flex items-center justify-center mx-auto mb-4">
            <Shield size={28} />
          </div>
          <h1 className="text-2xl font-extrabold text-gray-900">Admin Access</h1>
          <p className="text-sm text-gray-400 mt-1">Restricted area</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="relative">
            <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input data-testid="admin-email" type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="Admin email"
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-white border border-gray-200 text-sm text-gray-900 placeholder:text-gray-400 outline-none focus:border-gray-400 transition-all" />
          </div>
          <div className="relative">
            <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input data-testid="admin-password" type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="Admin password"
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-white border border-gray-200 text-sm text-gray-900 placeholder:text-gray-400 outline-none focus:border-gray-400 transition-all" />
          </div>
          {error && <p className="text-red-500 text-xs text-center">{error}</p>}
          <button data-testid="admin-submit" type="submit" disabled={loading}
            className="w-full py-3.5 rounded-xl bg-gray-900 text-white text-sm font-semibold flex items-center justify-center gap-2 hover:bg-gray-800 disabled:opacity-60 transition-all">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <>Sign In <ArrowRight size={16} /></>}
          </button>
        </form>
      </motion.div>
    </div>
  );
}
