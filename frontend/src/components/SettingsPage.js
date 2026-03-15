import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft, Settings, CreditCard, User, Sliders, Shield,
  LogOut, Pause, Trash2, Lock, Save, Loader2, Check, ChevronRight, ToggleLeft, ToggleRight
} from 'lucide-react';
import api from '@/api';

const TABS = [
  { key: 'subscription', label: 'Subscription', icon: CreditCard },
  { key: 'profile', label: 'Profile', icon: User },
  { key: 'preferences', label: 'Preferences', icon: Sliders },
  { key: 'account', label: 'Account', icon: Shield },
];

const INTERESTS = [
  'Technology', 'AI', 'Startups', 'Finance', 'Crypto',
  'Global News', 'Politics', 'Science', 'Business',
  'Internet Culture', 'Sports', 'Climate', 'Space', 'Health',
];

const DEPTH_OPTIONS = [
  { key: 'simple', label: 'Simple', desc: '30 second explanation', icon: '⚡' },
  { key: 'moderate', label: 'Moderate', desc: 'With context', icon: '📖' },
  { key: 'deep', label: 'Deep', desc: 'Data and analysis', icon: '🔬' },
];

export default function SettingsPage({ user, onBack, onLogout, onUserUpdate }) {
  const [tab, setTab] = useState('subscription');
  const [subInfo, setSubInfo] = useState(null);
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [mobile, setMobile] = useState(user?.mobile || '');
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [interests, setInterests] = useState(user?.preferences?.interests || []);
  const [depth, setDepth] = useState(user?.preferences?.explanation_depth || 'simple');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [confirmAction, setConfirmAction] = useState(null);

  useEffect(() => { loadSubInfo(); }, []);

  const loadSubInfo = async () => {
    try {
      const data = await api.getSubscriptionInfo();
      setSubInfo(data);
    } catch (e) { console.error(e); }
  };

  const showMsg = (msg) => { setMessage(msg); setError(''); setTimeout(() => setMessage(''), 3000); };
  const showErr = (msg) => { setError(msg); setMessage(''); setTimeout(() => setError(''), 3000); };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const res = await api.updateProfile({ name: name.trim(), email: email.trim() || undefined, mobile: mobile.trim() || undefined });
      if (onUserUpdate) onUserUpdate(res.user);
      showMsg('Profile updated');
    } catch (e) { showErr(e.response?.data?.detail || 'Failed to update'); }
    finally { setSaving(false); }
  };

  const handleChangePassword = async () => {
    if (newPw.length < 6) { showErr('Password must be at least 6 characters'); return; }
    setSaving(true);
    try {
      await api.changePassword({ current_password: currentPw, new_password: newPw });
      setCurrentPw(''); setNewPw('');
      showMsg('Password changed');
    } catch (e) { showErr(e.response?.data?.detail || 'Failed to change password'); }
    finally { setSaving(false); }
  };

  const handleSavePreferences = async () => {
    setSaving(true);
    try {
      await api.saveOnboarding({
        interests,
        curiosity_types: user?.preferences?.curiosity_types || [],
        explanation_depth: depth,
        country: user?.preferences?.country || '',
        region: user?.preferences?.region || '',
        professional_context: user?.preferences?.professional_context || '',
        followed_topics: user?.preferences?.followed_topics || [],
      });
      if (onUserUpdate) {
        const updated = { ...user, preferences: { ...user.preferences, interests, explanation_depth: depth } };
        onUserUpdate(updated);
      }
      showMsg('Preferences saved');
    } catch (e) { showErr('Failed to save preferences'); }
    finally { setSaving(false); }
  };

  const handleToggleAutoRenew = async () => {
    try {
      const res = await api.toggleAutoRenew();
      setSubInfo(prev => ({ ...prev, auto_renew: res.auto_renew }));
      showMsg(`Auto-renew ${res.auto_renew ? 'enabled' : 'disabled'}`);
    } catch (e) { showErr('Failed to toggle auto-renew'); }
  };

  const handleSubscribe = async () => {
    try {
      const res = await api.createCheckout(window.location.origin);
      window.location.href = res.url;
    } catch (e) { showErr('Failed to start checkout'); }
  };

  const handleSuspend = async () => {
    try { await api.suspendAccount(); onLogout(); } catch (e) { showErr('Failed'); }
  };

  const handleDelete = async () => {
    try { await api.deleteAccount(); onLogout(); } catch (e) { showErr('Failed'); }
  };

  const toggleInterest = (item) => {
    setInterests(prev => prev.includes(item) ? prev.filter(i => i !== item) : [...prev, item]);
  };

  const trialDaysLeft = subInfo?.trial_end
    ? Math.max(0, Math.ceil((new Date(subInfo.trial_end) - Date.now()) / 86400000))
    : 0;

  return (
    <div data-testid="settings-page" className="min-h-screen pb-24">
      {/* Header */}
      <div className="px-5 pt-5 pb-3">
        <div className="flex items-center gap-3 mb-4">
          <button data-testid="settings-back" onClick={onBack}
            className="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition-colors">
            <ArrowLeft size={18} className="text-gray-600" />
          </button>
          <h1 className="text-xl font-extrabold text-gray-900">Settings</h1>
        </div>

        {/* Tab pills */}
        <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-hide">
          {TABS.map(t => (
            <button key={t.key} data-testid={`settings-tab-${t.key}`} onClick={() => setTab(t.key)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all
                ${tab === t.key ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
              <t.icon size={14} />{t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Feedback */}
      <AnimatePresence>
        {message && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="mx-5 mb-3 px-4 py-2 rounded-xl bg-green-50 text-green-700 text-xs font-medium text-center">{message}</motion.div>
        )}
        {error && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="mx-5 mb-3 px-4 py-2 rounded-xl bg-red-50 text-red-600 text-xs font-medium text-center">{error}</motion.div>
        )}
      </AnimatePresence>

      <div className="px-5 mt-3">
        <AnimatePresence mode="wait">
          {/* SUBSCRIPTION */}
          {tab === 'subscription' && (
            <motion.div key="sub" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="bg-white rounded-2xl border border-gray-100 p-5 mb-4">
                <p className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-3">Current Plan</p>
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-lg font-bold text-gray-900 capitalize">
                      {subInfo?.subscription_status === 'active' ? 'Premium' : subInfo?.subscription_status === 'trial' ? 'Free Trial' : 'Expired'}
                    </p>
                    {subInfo?.subscription_status === 'trial' && (
                      <p className="text-xs text-gray-400">{trialDaysLeft} day{trialDaysLeft !== 1 ? 's' : ''} remaining</p>
                    )}
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold
                    ${subInfo?.subscription_status === 'active' ? 'bg-green-50 text-green-600'
                      : subInfo?.subscription_status === 'trial' ? 'bg-blue-50 text-blue-600'
                      : 'bg-red-50 text-red-600'}`}>
                    {subInfo?.subscription_status === 'active' ? 'Active' : subInfo?.subscription_status === 'trial' ? 'Trial' : 'Expired'}
                  </span>
                </div>
                {subInfo?.subscription_status !== 'active' && (
                  <button data-testid="subscribe-btn" onClick={handleSubscribe}
                    className="w-full py-3 rounded-xl bg-gray-900 text-white text-sm font-semibold hover:bg-gray-800 transition-all">
                    Subscribe — $4.99/month
                  </button>
                )}
              </div>

              <div className="bg-white rounded-2xl border border-gray-100 p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">Auto-renew</p>
                    <p className="text-xs text-gray-400">Automatically renew your subscription</p>
                  </div>
                  <button data-testid="auto-renew-toggle" onClick={handleToggleAutoRenew}
                    className="text-gray-900">
                    {subInfo?.auto_renew
                      ? <ToggleRight size={32} className="text-green-500" />
                      : <ToggleLeft size={32} className="text-gray-300" />}
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {/* PROFILE */}
          {tab === 'profile' && (
            <motion.div key="profile" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
              <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-3">
                <p className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-1">Personal Info</p>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Name</label>
                  <input data-testid="profile-name" value={name} onChange={e => setName(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl bg-gray-50 border border-gray-200 text-sm outline-none focus:border-gray-400 transition-all" />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Email</label>
                  <input data-testid="profile-email" value={email} onChange={e => setEmail(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl bg-gray-50 border border-gray-200 text-sm outline-none focus:border-gray-400 transition-all" />
                </div>
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Mobile</label>
                  <input data-testid="profile-mobile" value={mobile} onChange={e => setMobile(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl bg-gray-50 border border-gray-200 text-sm outline-none focus:border-gray-400 transition-all" />
                </div>
                <button data-testid="profile-save" onClick={handleSaveProfile} disabled={saving}
                  className="w-full py-3 rounded-xl bg-gray-900 text-white text-sm font-semibold flex items-center justify-center gap-2 hover:bg-gray-800 disabled:opacity-60 transition-all">
                  {saving ? <Loader2 size={16} className="animate-spin" /> : <><Save size={14} /> Save Changes</>}
                </button>
              </div>

              <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-3">
                <p className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-1">Change Password</p>
                <input data-testid="profile-current-pw" type="password" value={currentPw} onChange={e => setCurrentPw(e.target.value)}
                  placeholder="Current password"
                  className="w-full px-3 py-2.5 rounded-xl bg-gray-50 border border-gray-200 text-sm outline-none focus:border-gray-400 transition-all" />
                <input data-testid="profile-new-pw" type="password" value={newPw} onChange={e => setNewPw(e.target.value)}
                  placeholder="New password (min 6 chars)"
                  className="w-full px-3 py-2.5 rounded-xl bg-gray-50 border border-gray-200 text-sm outline-none focus:border-gray-400 transition-all" />
                <button data-testid="profile-change-pw" onClick={handleChangePassword} disabled={saving || !currentPw || !newPw}
                  className="w-full py-3 rounded-xl bg-gray-900 text-white text-sm font-semibold flex items-center justify-center gap-2 hover:bg-gray-800 disabled:opacity-60 transition-all">
                  <Lock size={14} /> Change Password
                </button>
              </div>
            </motion.div>
          )}

          {/* PREFERENCES */}
          {tab === 'preferences' && (
            <motion.div key="prefs" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
              <div className="bg-white rounded-2xl border border-gray-100 p-5">
                <p className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-3">Your Interests</p>
                <div className="flex flex-wrap gap-2 mb-4">
                  {INTERESTS.map(item => (
                    <button key={item} onClick={() => toggleInterest(item)}
                      className={`px-3 py-2 rounded-xl text-xs font-medium transition-all
                        ${interests.includes(item) ? 'bg-gray-900 text-white' : 'bg-gray-50 border border-gray-200 text-gray-600 hover:border-gray-300'}`}>
                      {interests.includes(item) && <Check size={12} className="inline mr-1" />}{item}
                    </button>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-gray-100 p-5">
                <p className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-3">Explanation Depth</p>
                <div className="space-y-2">
                  {DEPTH_OPTIONS.map(opt => (
                    <button key={opt.key} onClick={() => setDepth(opt.key)}
                      className={`w-full text-left px-4 py-3 rounded-xl text-sm flex items-center gap-3 transition-all
                        ${depth === opt.key ? 'bg-gray-900 text-white' : 'bg-gray-50 border border-gray-200 text-gray-700 hover:border-gray-300'}`}>
                      <span>{opt.icon}</span>
                      <div>
                        <p className="font-medium">{opt.label}</p>
                        <p className={`text-[10px] ${depth === opt.key ? 'text-gray-300' : 'text-gray-400'}`}>{opt.desc}</p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <button data-testid="prefs-save" onClick={handleSavePreferences} disabled={saving}
                className="w-full py-3 rounded-xl bg-gray-900 text-white text-sm font-semibold flex items-center justify-center gap-2 hover:bg-gray-800 disabled:opacity-60 transition-all">
                {saving ? <Loader2 size={16} className="animate-spin" /> : <><Save size={14} /> Save Preferences</>}
              </button>
            </motion.div>
          )}

          {/* ACCOUNT */}
          {tab === 'account' && (
            <motion.div key="account" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-3">
              <button data-testid="account-signout" onClick={onLogout}
                className="w-full bg-white rounded-2xl border border-gray-100 p-4 flex items-center gap-3 text-left hover:bg-gray-50 transition-colors">
                <LogOut size={18} className="text-gray-500" />
                <div className="flex-1"><p className="text-sm font-semibold text-gray-900">Sign Out</p><p className="text-xs text-gray-400">Log out of your account</p></div>
                <ChevronRight size={16} className="text-gray-300" />
              </button>

              <button data-testid="account-suspend" onClick={() => setConfirmAction('suspend')}
                className="w-full bg-white rounded-2xl border border-gray-100 p-4 flex items-center gap-3 text-left hover:bg-gray-50 transition-colors">
                <Pause size={18} className="text-yellow-500" />
                <div className="flex-1"><p className="text-sm font-semibold text-gray-900">Suspend Account</p><p className="text-xs text-gray-400">Temporarily disable your account</p></div>
                <ChevronRight size={16} className="text-gray-300" />
              </button>

              <button data-testid="account-delete" onClick={() => setConfirmAction('delete')}
                className="w-full bg-white rounded-2xl border border-red-100 p-4 flex items-center gap-3 text-left hover:bg-red-50 transition-colors">
                <Trash2 size={18} className="text-red-500" />
                <div className="flex-1"><p className="text-sm font-semibold text-red-600">Delete Account</p><p className="text-xs text-gray-400">Permanently remove your account and data</p></div>
                <ChevronRight size={16} className="text-gray-300" />
              </button>

              {/* Confirm modal */}
              <AnimatePresence>
                {confirmAction && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[60] flex items-center justify-center p-5"
                    onClick={() => setConfirmAction(null)}>
                    <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }}
                      onClick={e => e.stopPropagation()}
                      className="bg-white rounded-2xl p-6 w-full max-w-sm">
                      <h3 className="text-lg font-bold text-gray-900 mb-2">
                        {confirmAction === 'suspend' ? 'Suspend account?' : 'Delete account?'}
                      </h3>
                      <p className="text-sm text-gray-400 mb-5">
                        {confirmAction === 'suspend'
                          ? 'Your account will be temporarily disabled. You can reactivate it by contacting support.'
                          : 'This action is permanent. All your data, saved topics, and preferences will be deleted forever.'}
                      </p>
                      <div className="flex gap-2">
                        <button onClick={() => setConfirmAction(null)}
                          className="flex-1 py-3 rounded-xl bg-gray-100 text-gray-700 text-sm font-semibold hover:bg-gray-200 transition-all">Cancel</button>
                        <button data-testid="confirm-action"
                          onClick={() => { confirmAction === 'suspend' ? handleSuspend() : handleDelete(); setConfirmAction(null); }}
                          className={`flex-1 py-3 rounded-xl text-white text-sm font-semibold transition-all
                            ${confirmAction === 'delete' ? 'bg-red-600 hover:bg-red-700' : 'bg-yellow-600 hover:bg-yellow-700'}`}>
                          {confirmAction === 'suspend' ? 'Suspend' : 'Delete Forever'}
                        </button>
                      </div>
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
