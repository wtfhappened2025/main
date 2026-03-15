import { useState, useCallback, useEffect } from 'react';
import '@/App.css';
import AuthScreen from '@/components/AuthScreen';
import OnboardingFlow from '@/components/OnboardingFlow';
import TrendingFeed from '@/components/TrendingFeed';
import ExplanationView from '@/components/ExplanationView';
import ExplainInput from '@/components/ExplainInput';
import SavedTopics from '@/components/SavedTopics';
import BottomNav from '@/components/BottomNav';
import SocialCardPreview from '@/components/SocialCardPreview';
import { AnimatePresence, motion } from 'framer-motion';
import { LogOut, User } from 'lucide-react';
import api from '@/api';

function App() {
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [activeTab, setActiveTab] = useState('trending');
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [socialCard, setSocialCard] = useState(null);
  const [showProfile, setShowProfile] = useState(false);

  // Check for existing session on mount
  useEffect(() => {
    const stored = localStorage.getItem('wtf_user');
    const token = localStorage.getItem('wtf_token');
    if (stored && token) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem('wtf_user');
        localStorage.removeItem('wtf_token');
      }
    }
    setAuthChecked(true);

    // Listen for auth expiry
    const handleExpiry = () => { setUser(null); };
    window.addEventListener('auth_expired', handleExpiry);
    return () => window.removeEventListener('auth_expired', handleExpiry);
  }, []);

  const handleAuthSuccess = useCallback((userData) => {
    setUser(userData);
  }, []);

  const handleOnboardingComplete = useCallback((updatedUser) => {
    setUser(updatedUser);
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem('wtf_token');
    localStorage.removeItem('wtf_user');
    setUser(null);
    setShowProfile(false);
    setSelectedTopic(null);
    setActiveTab('trending');
  }, []);

  const handleTopicClick = useCallback((topic) => {
    setSelectedTopic(topic);
  }, []);

  const handleBack = useCallback(() => {
    setSelectedTopic(null);
  }, []);

  const handleShare = useCallback(async (topic) => {
    try {
      const data = await api.getRenderCard(topic.id);
      setSocialCard(data.card_data);
    } catch (e) {
      console.error('Failed to load social card:', e);
    }
  }, []);

  const handleExplained = useCallback((topic) => {
    setSelectedTopic(topic);
  }, []);

  const handleTabChange = useCallback((tab) => {
    setSelectedTopic(null);
    setActiveTab(tab);
  }, []);

  // Loading state
  if (!authChecked) {
    return (
      <div className="app-shell flex items-center justify-center min-h-screen">
        <div className="w-12 h-12 rounded-2xl bg-gray-900 text-white flex items-center justify-center
          text-xl font-black animate-pulse">
          W
        </div>
      </div>
    );
  }

  // Not logged in
  if (!user) {
    return (
      <div className="app-shell">
        <AuthScreen onAuthSuccess={handleAuthSuccess} />
      </div>
    );
  }

  // Onboarding not complete
  if (!user.onboarding_complete) {
    return (
      <div className="app-shell">
        <OnboardingFlow user={user} onComplete={handleOnboardingComplete} />
      </div>
    );
  }

  // Main app
  return (
    <div className="app-shell">
      {/* Profile menu button */}
      <div className="fixed top-4 right-4 z-40" style={{ maxWidth: '480px' }}>
        <button
          data-testid="profile-btn"
          onClick={() => setShowProfile(!showProfile)}
          className="w-9 h-9 rounded-full bg-white border border-gray-200 shadow-sm
            flex items-center justify-center hover:shadow-md transition-all"
        >
          <User size={16} className="text-gray-600" />
        </button>
        <AnimatePresence>
          {showProfile && (
            <motion.div
              initial={{ opacity: 0, y: -5, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -5, scale: 0.95 }}
              className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-lg border border-gray-100
                overflow-hidden"
              data-testid="profile-menu"
            >
              <div className="px-4 py-3 border-b border-gray-50">
                <p className="text-sm font-semibold text-gray-900 truncate">{user.name}</p>
                <p className="text-xs text-gray-400 truncate">{user.email || user.mobile}</p>
              </div>
              <button
                data-testid="logout-btn"
                onClick={handleLogout}
                className="w-full px-4 py-3 text-left text-sm text-red-500 hover:bg-red-50
                  flex items-center gap-2 transition-colors"
              >
                <LogOut size={14} />
                Sign Out
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence mode="wait">
        {selectedTopic ? (
          <motion.div
            key="explanation"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            <ExplanationView
              topic={selectedTopic}
              onBack={handleBack}
              onShare={handleShare}
            />
          </motion.div>
        ) : (
          <motion.div
            key={activeTab}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
          >
            {activeTab === 'trending' && (
              <TrendingFeed onTopicClick={handleTopicClick} />
            )}
            {activeTab === 'explain' && (
              <ExplainInput onExplained={handleExplained} />
            )}
            {activeTab === 'saved' && (
              <SavedTopics onTopicClick={handleTopicClick} />
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <BottomNav activeTab={activeTab} onTabChange={handleTabChange} />

      <AnimatePresence>
        {socialCard && (
          <SocialCardPreview
            cardData={socialCard}
            onClose={() => setSocialCard(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
