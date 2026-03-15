import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, Phone, Lock, User, Eye, EyeOff, ArrowRight, Loader2 } from 'lucide-react';
import api from '@/api';

export default function AuthScreen({ onAuthSuccess, onForgotPassword }) {
  const [mode, setMode] = useState('login'); // login | register
  const [authMethod, setAuthMethod] = useState('email'); // email | mobile
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [mobile, setMobile] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let result;
      if (mode === 'register') {
        if (!name.trim()) { setError('Name is required'); setLoading(false); return; }
        if (authMethod === 'email' && !email.trim()) { setError('Email is required'); setLoading(false); return; }
        if (authMethod === 'mobile' && !mobile.trim()) { setError('Mobile is required'); setLoading(false); return; }
        if (password.length < 6) { setError('Password must be at least 6 characters'); setLoading(false); return; }

        result = await api.register({
          name: name.trim(),
          email: authMethod === 'email' ? email.trim() : undefined,
          mobile: authMethod === 'mobile' ? mobile.trim() : undefined,
          password,
        });
      } else {
        const identifier = authMethod === 'email' ? email.trim() : mobile.trim();
        if (!identifier) { setError('Email or mobile is required'); setLoading(false); return; }
        if (!password) { setError('Password is required'); setLoading(false); return; }

        result = await api.login({ identifier, password });
      }

      localStorage.setItem('wtf_token', result.token);
      localStorage.setItem('wtf_user', JSON.stringify(result.user));
      onAuthSuccess(result.user);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Something went wrong';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="auth-screen" className="min-h-screen flex items-center justify-center px-5 py-10">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-sm"
      >
        {/* Logo / Brand */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200 }}
            className="w-16 h-16 rounded-2xl bg-gray-900 text-white flex items-center justify-center mx-auto mb-4
              text-2xl font-black"
          >
            W
          </motion.div>
          <h1 className="text-2xl font-extrabold text-gray-900">WTFHappened</h1>
          <p className="text-sm text-gray-400 mt-1">
            {mode === 'login' ? 'Welcome back' : 'Create your account'}
          </p>
        </div>

        {/* Auth method toggle */}
        <div className="flex bg-gray-100 rounded-xl p-1 mb-5">
          <button
            data-testid="auth-method-email"
            onClick={() => setAuthMethod('email')}
            className={`flex-1 py-2 rounded-lg text-xs font-semibold transition-all duration-200
              ${authMethod === 'email' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'}`}
          >
            <Mail size={14} className="inline mr-1.5" />Email
          </button>
          <button
            data-testid="auth-method-mobile"
            onClick={() => setAuthMethod('mobile')}
            className={`flex-1 py-2 rounded-lg text-xs font-semibold transition-all duration-200
              ${authMethod === 'mobile' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'}`}
          >
            <Phone size={14} className="inline mr-1.5" />Mobile
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {/* Name (register only) */}
          <AnimatePresence>
            {mode === 'register' && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
              >
                <div className="relative">
                  <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    data-testid="auth-name"
                    type="text"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="Your name"
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-white border border-gray-200
                      text-sm text-gray-900 placeholder:text-gray-400 outline-none
                      focus:border-gray-400 focus:shadow-sm transition-all"
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Email or Mobile */}
          {authMethod === 'email' ? (
            <div className="relative">
              <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                data-testid="auth-email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="Email address"
                className="w-full pl-10 pr-4 py-3 rounded-xl bg-white border border-gray-200
                  text-sm text-gray-900 placeholder:text-gray-400 outline-none
                  focus:border-gray-400 focus:shadow-sm transition-all"
              />
            </div>
          ) : (
            <div className="relative">
              <Phone size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                data-testid="auth-mobile"
                type="tel"
                value={mobile}
                onChange={e => setMobile(e.target.value)}
                placeholder="Mobile number"
                className="w-full pl-10 pr-4 py-3 rounded-xl bg-white border border-gray-200
                  text-sm text-gray-900 placeholder:text-gray-400 outline-none
                  focus:border-gray-400 focus:shadow-sm transition-all"
              />
            </div>
          )}

          {/* Password */}
          <div className="relative">
            <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              data-testid="auth-password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full pl-10 pr-10 py-3 rounded-xl bg-white border border-gray-200
                text-sm text-gray-900 placeholder:text-gray-400 outline-none
                focus:border-gray-400 focus:shadow-sm transition-all"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>

          {/* Error */}
          <AnimatePresence>
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="text-red-500 text-xs text-center py-1"
                data-testid="auth-error"
              >
                {error}
              </motion.p>
            )}
          </AnimatePresence>

          {/* Submit */}
          <button
            data-testid="auth-submit"
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-gray-900 text-white text-sm font-semibold
              flex items-center justify-center gap-2 hover:bg-gray-800
              disabled:opacity-60 transition-all duration-200"
          >
            {loading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <>
                {mode === 'login' ? 'Sign In' : 'Create Account'}
                <ArrowRight size={16} />
              </>
            )}
          </button>

          {/* T&C for register */}
          {mode === 'register' && (
            <p className="text-[11px] text-gray-400 text-center mt-3">
              By signing up, you accept our{' '}
              <button data-testid="terms-link" onClick={() => window.open('/terms', '_blank')}
                className="text-gray-600 underline hover:text-gray-900">Terms & Conditions</button>
            </p>
          )}

          {/* Forgot password for login */}
          {mode === 'login' && (
            <button data-testid="forgot-password-link" type="button" onClick={onForgotPassword}
              className="w-full text-center text-xs text-gray-400 hover:text-gray-600 mt-3 transition-colors">
              Forgot password?
            </button>
          )}
        </form>

        {/* Toggle mode */}
        <p className="text-center text-sm text-gray-400 mt-5">
          {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}
          <button
            data-testid="auth-toggle-mode"
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}
            className="ml-1.5 text-gray-900 font-semibold hover:underline"
          >
            {mode === 'login' ? 'Sign Up' : 'Sign In'}
          </button>
        </p>
      </motion.div>
    </div>
  );
}
