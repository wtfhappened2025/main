import { useState, useCallback, useEffect } from 'react';
import '@/App.css';
import AuthScreen from '@/components/AuthScreen';
import ForgotPassword from '@/components/ForgotPassword';
import OnboardingFlow from '@/components/OnboardingFlow';
import TrendingFeed from '@/components/TrendingFeed';
import ExplanationView from '@/components/ExplanationView';
import ExplainInput from '@/components/ExplainInput';
import SavedTopics from '@/components/SavedTopics';
import BottomNav from '@/components/BottomNav';
import SocialCardPreview from '@/components/SocialCardPreview';
import SettingsPage from '@/components/SettingsPage';
import TermsPage from '@/components/TermsPage';
import AdminLogin from '@/components/AdminLogin';
import AdminPanel from '@/components/AdminPanel';
import { AnimatePresence, motion } from 'framer-motion';
import { Settings, User } from 'lucide-react';
import api from '@/api';

function App() {
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [view, setView] = useState('auth'); // auth | forgot | terms | onboarding | main | settings | admin-login | admin
  const [activeTab, setActiveTab] = useState('trending');
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [socialCard, setSocialCard] = useState(null);
  const [showProfile, setShowProfile] = useState(false);

  // Check for existing session on mount
  useEffect(() => {
    const stored = localStorage.getItem('wtf_user');
    const token = localStorage.getItem('wtf_token');
    const adminToken = localStorage.getItem('wtf_admin_token');
    const path = window.location.pathname;

    // Hidden admin route: /admin
    if (path === '/admin') {
      if (adminToken) {
        setView('admin');
      } else {
        setView('admin-login');
      }
      setAuthChecked(true);
      return;
    }

    // Terms page route: /terms
    if (path === '/terms') {
      setView('terms');
      setAuthChecked(true);
      return;
    }

    // Check URL for payment callback
    const params = new URLSearchParams(window.location.search);
    if (params.get('payment') === 'success') {
      const sessionId = params.get('session_id');
      if (sessionId) {
        handlePaymentSuccess(sessionId);
      }
      window.history.replaceState({}, '', window.location.pathname);
    }

    if (adminToken && path === '/admin') {
      setView('admin');
      setAuthChecked(true);
      return;
    }

    if (stored && token) {
      try {
        const userData = JSON.parse(stored);
        setUser(userData);
        setView(userData.onboarding_complete ? 'main' : 'onboarding');
      } catch {
        localStorage.removeItem('wtf_user');
        localStorage.removeItem('wtf_token');
      }
    }
    setAuthChecked(true);

    const handleExpiry = () => { setUser(null); setView('auth'); };
    window.addEventListener('auth_expired', handleExpiry);
    return () => window.removeEventListener('auth_expired', handleExpiry);
  }, []);

  const handlePaymentSuccess = async (sessionId) => {
    try {
      const res = await api.checkPaymentStatus(sessionId);
      if (res.payment_status === 'paid') {
        const stored = localStorage.getItem('wtf_user');
        if (stored) {
          const userData = JSON.parse(stored);
          userData.subscription_status = 'active';
          localStorage.setItem('wtf_user', JSON.stringify(userData));
          setUser(userData);
        }
      }
    } catch (e) { console.error('Payment check failed:', e); }
  };

  const handleAuthSuccess = useCallback((userData) => {
    setUser(userData);
    setView(userData.onboarding_complete ? 'main' : 'onboarding');
  }, []);

  const handleOnboardingComplete = useCallback((updatedUser) => {
    setUser(updatedUser);
    setView('main');
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem('wtf_token');
    localStorage.removeItem('wtf_user');
    setUser(null);
    setView('auth');
    setShowProfile(false);
    setSelectedTopic(null);
    setActiveTab('trending');
  }, []);

  const handleAdminLogout = useCallback(() => {
    localStorage.removeItem('wtf_admin_token');
    window.history.pushState({}, '', '/');
    setView('auth');
  }, []);

  const handleUserUpdate = useCallback((updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem('wtf_user', JSON.stringify(updatedUser));
  }, []);

  const handleTopicClick = useCallback((topic) => { setSelectedTopic(topic); }, []);
  const handleBack = useCallback(() => { setSelectedTopic(null); }, []);

  const handleShare = useCallback(async (topic) => {
    try {
      const data = await api.getRenderCard(topic.id);
      setSocialCard(data.card_data);
    } catch (e) { console.error('Failed to load social card:', e); }
  }, []);

  const handleExplained = useCallback((topic) => { setSelectedTopic(topic); }, []);
  const handleTabChange = useCallback((tab) => { setSelectedTopic(null); setActiveTab(tab); }, []);

  // Loading
  if (!authChecked) {
    return (
      <div className="app-shell flex items-center justify-center min-h-screen">
        <div className="w-12 h-12 rounded-2xl bg-gray-900 text-white flex items-center justify-center text-xl font-black animate-pulse">W</div>
      </div>
    );
  }

  // Terms page (standalone)
  if (view === 'terms') {
    return <div className="app-shell"><TermsPage onBack={() => setView('auth')} /></div>;
  }

  // Admin login — only accessible via /admin route
  if (view === 'admin-login') {
    return <div className="app-shell"><AdminLogin onBack={() => { window.history.pushState({}, '', '/'); setView('auth'); }} onAdminAuth={() => setView('admin')} /></div>;
  }

  // Admin panel
  if (view === 'admin') {
    return <AdminPanel onLogout={handleAdminLogout} />;
  }

  // Forgot password
  if (view === 'forgot') {
    return <div className="app-shell"><ForgotPassword onBack={() => setView('auth')} /></div>;
  }

  // Auth
  if (!user || view === 'auth') {
    return (
      <div className="app-shell">
        <AuthScreen
          onAuthSuccess={handleAuthSuccess}
          onForgotPassword={() => setView('forgot')}
        />
      </div>
    );
  }

  // Onboarding
  if (view === 'onboarding' || !user.onboarding_complete) {
    return <div className="app-shell"><OnboardingFlow user={user} onComplete={handleOnboardingComplete} /></div>;
  }

  // Settings
  if (view === 'settings') {
    return (
      <div className="app-shell">
        <SettingsPage
          user={user}
          onBack={() => setView('main')}
          onLogout={handleLogout}
          onUserUpdate={handleUserUpdate}
        />
      </div>
    );
  }

  // Main app
  return (
    <div className="app-shell">
      {/* Top-right profile/settings */}
      <div className="fixed top-4 right-4 z-40 flex gap-2">
        <button data-testid="settings-btn" onClick={() => setView('settings')}
          className="w-9 h-9 rounded-full bg-white border border-gray-200 shadow-sm flex items-center justify-center hover:shadow-md transition-all">
          <Settings size={16} className="text-gray-600" />
        </button>
        <button data-testid="profile-btn" onClick={() => setShowProfile(!showProfile)}
          className="w-9 h-9 rounded-full bg-white border border-gray-200 shadow-sm flex items-center justify-center hover:shadow-md transition-all relative">
          <User size={16} className="text-gray-600" />
        </button>
        <AnimatePresence>
          {showProfile && (
            <motion.div initial={{ opacity: 0, y: -5, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -5, scale: 0.95 }}
              className="absolute right-0 top-12 w-56 bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden"
              data-testid="profile-menu">
              <div className="px-4 py-3 border-b border-gray-50">
                <p className="text-sm font-semibold text-gray-900 truncate">{user.name}</p>
                <p className="text-xs text-gray-400 truncate">{user.email || user.mobile}</p>
                <span className={`inline-block mt-1 text-[9px] font-bold px-1.5 py-0.5 rounded uppercase
                  ${user.subscription_status === 'active' ? 'bg-green-50 text-green-600'
                    : user.subscription_status === 'trial' ? 'bg-blue-50 text-blue-600'
                    : 'bg-red-50 text-red-600'}`}>
                  {user.subscription_status || 'trial'}
                </span>
              </div>
              <button data-testid="profile-settings" onClick={() => { setShowProfile(false); setView('settings'); }}
                className="w-full px-4 py-3 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2 transition-colors">
                <Settings size={14} /> Settings
              </button>
              <button data-testid="logout-btn" onClick={handleLogout}
                className="w-full px-4 py-3 text-left text-sm text-red-500 hover:bg-red-50 flex items-center gap-2 transition-colors border-t border-gray-50">
                Sign Out
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence mode="wait">
        {selectedTopic ? (
          <motion.div key="explanation" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.2 }}>
            <ExplanationView topic={selectedTopic} onBack={handleBack} onShare={handleShare} />
          </motion.div>
        ) : (
          <motion.div key={activeTab} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }}>
            {activeTab === 'trending' && <TrendingFeed onTopicClick={handleTopicClick} />}
            {activeTab === 'explain' && <ExplainInput onExplained={handleExplained} />}
            {activeTab === 'saved' && <SavedTopics onTopicClick={handleTopicClick} />}
          </motion.div>
        )}
      </AnimatePresence>

      <BottomNav activeTab={activeTab} onTabChange={handleTabChange} />

      <AnimatePresence>
        {socialCard && <SocialCardPreview cardData={socialCard} onClose={() => setSocialCard(null)} />}
      </AnimatePresence>
    </div>
  );
}

export default App;
