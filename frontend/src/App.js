import { useState, useCallback } from 'react';
import '@/App.css';
import TrendingFeed from '@/components/TrendingFeed';
import ExplanationView from '@/components/ExplanationView';
import ExplainInput from '@/components/ExplainInput';
import SavedTopics from '@/components/SavedTopics';
import BottomNav from '@/components/BottomNav';
import SocialCardPreview from '@/components/SocialCardPreview';
import { AnimatePresence, motion } from 'framer-motion';
import api from '@/api';

function App() {
  const [activeTab, setActiveTab] = useState('trending');
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [socialCard, setSocialCard] = useState(null);

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

  const handleExplained = useCallback((topic, explanation) => {
    setSelectedTopic(topic);
  }, []);

  const handleTabChange = useCallback((tab) => {
    setSelectedTopic(null);
    setActiveTab(tab);
  }, []);

  return (
    <div className="app-shell">
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

      {/* Bottom navigation */}
      <BottomNav activeTab={activeTab} onTabChange={handleTabChange} />

      {/* Social card preview overlay */}
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
