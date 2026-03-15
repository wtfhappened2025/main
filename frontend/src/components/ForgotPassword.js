import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Mail, Phone, Lock, Loader2, Check } from 'lucide-react';
import api from '@/api';

export default function ForgotPassword({ onBack }) {
  const [step, setStep] = useState('request'); // request | token | done
  const [authMethod, setAuthMethod] = useState('email');
  const [identifier, setIdentifier] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const handleRequestReset = async (e) => {
    e.preventDefault();
    if (!identifier.trim()) { setError('Please enter your email or mobile'); return; }
    setLoading(true); setError('');
    try {
      const res = await api.forgotPassword(identifier.trim());
      setMessage(res.message);
      // For demo, show the token if returned
      if (res.reset_token) setResetToken(res.reset_token);
      setStep('token');
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong');
    } finally { setLoading(false); }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (!resetToken.trim()) { setError('Please enter the reset token'); return; }
    if (newPassword.length < 6) { setError('Password must be at least 6 characters'); return; }
    setLoading(true); setError('');
    try {
      await api.resetPassword(resetToken.trim(), newPassword);
      setStep('done');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid or expired token');
    } finally { setLoading(false); }
  };

  return (
    <div data-testid="forgot-password" className="min-h-screen flex items-center justify-center px-5 py-10">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm">
        <button data-testid="forgot-back" onClick={onBack}
          className="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center mb-6 hover:bg-gray-200 transition-colors">
          <ArrowLeft size={18} className="text-gray-600" />
        </button>

        <AnimatePresence mode="wait">
          {step === 'request' && (
            <motion.div key="request" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <h2 className="text-xl font-extrabold text-gray-900 mb-1">Reset password</h2>
              <p className="text-sm text-gray-400 mb-6">Enter your email or mobile to receive a reset link.</p>

              <div className="flex bg-gray-100 rounded-xl p-1 mb-4">
                <button data-testid="forgot-method-email" onClick={() => setAuthMethod('email')}
                  className={`flex-1 py-2 rounded-lg text-xs font-semibold transition-all ${authMethod === 'email' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'}`}>
                  <Mail size={14} className="inline mr-1.5" />Email
                </button>
                <button data-testid="forgot-method-mobile" onClick={() => setAuthMethod('mobile')}
                  className={`flex-1 py-2 rounded-lg text-xs font-semibold transition-all ${authMethod === 'mobile' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'}`}>
                  <Phone size={14} className="inline mr-1.5" />Mobile
                </button>
              </div>

              <form onSubmit={handleRequestReset}>
                <div className="relative mb-3">
                  {authMethod === 'email'
                    ? <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                    : <Phone size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />}
                  <input data-testid="forgot-identifier" type={authMethod === 'email' ? 'email' : 'tel'}
                    value={identifier} onChange={e => setIdentifier(e.target.value)}
                    placeholder={authMethod === 'email' ? 'Email address' : 'Mobile number'}
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-white border border-gray-200 text-sm text-gray-900 placeholder:text-gray-400 outline-none focus:border-gray-400 transition-all" />
                </div>
                {error && <p data-testid="forgot-error" className="text-red-500 text-xs text-center mb-3">{error}</p>}
                <button data-testid="forgot-submit" type="submit" disabled={loading}
                  className="w-full py-3.5 rounded-xl bg-gray-900 text-white text-sm font-semibold flex items-center justify-center gap-2 hover:bg-gray-800 disabled:opacity-60 transition-all">
                  {loading ? <Loader2 size={18} className="animate-spin" /> : 'Send Reset Link'}
                </button>
              </form>
            </motion.div>
          )}

          {step === 'token' && (
            <motion.div key="token" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <h2 className="text-xl font-extrabold text-gray-900 mb-1">Enter reset token</h2>
              <p className="text-sm text-gray-400 mb-6">{message}</p>
              <form onSubmit={handleResetPassword} className="space-y-3">
                <input data-testid="reset-token-input" type="text" value={resetToken}
                  onChange={e => setResetToken(e.target.value)} placeholder="Paste reset token"
                  className="w-full px-4 py-3 rounded-xl bg-white border border-gray-200 text-sm text-gray-900 placeholder:text-gray-400 outline-none focus:border-gray-400 transition-all" />
                <div className="relative">
                  <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input data-testid="reset-new-password" type="password" value={newPassword}
                    onChange={e => setNewPassword(e.target.value)} placeholder="New password (min 6 chars)"
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-white border border-gray-200 text-sm text-gray-900 placeholder:text-gray-400 outline-none focus:border-gray-400 transition-all" />
                </div>
                {error && <p className="text-red-500 text-xs text-center">{error}</p>}
                <button data-testid="reset-submit" type="submit" disabled={loading}
                  className="w-full py-3.5 rounded-xl bg-gray-900 text-white text-sm font-semibold flex items-center justify-center gap-2 hover:bg-gray-800 disabled:opacity-60 transition-all">
                  {loading ? <Loader2 size={18} className="animate-spin" /> : 'Reset Password'}
                </button>
              </form>
            </motion.div>
          )}

          {step === 'done' && (
            <motion.div key="done" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-10">
              <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                <Check size={28} className="text-green-600" />
              </div>
              <h2 className="text-xl font-extrabold text-gray-900 mb-2">Password reset!</h2>
              <p className="text-sm text-gray-400 mb-6">You can now sign in with your new password.</p>
              <button data-testid="reset-back-to-login" onClick={onBack}
                className="px-8 py-3 rounded-xl bg-gray-900 text-white text-sm font-semibold hover:bg-gray-800 transition-all">
                Back to Sign In
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
