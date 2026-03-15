import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, Sparkles } from 'lucide-react';
import TopicCard from './TopicCard';
import api from '@/api';

const CATEGORIES = [
  { key: 'for-you', label: 'For You' },
  { key: 'all', label: 'All' },
  { key: 'finance', label: 'Markets' },
  { key: 'technology', label: 'Tech' },
  { key: 'ai', label: 'AI' },
  { key: 'economy', label: 'Economy' },
  { key: 'crypto', label: 'Crypto' },
  { key: 'science', label: 'Science' },
  { key: 'entertainment', label: 'Celeb' },
  { key: 'lifestyle', label: 'Style' },
];

export default function TrendingFeed({ onTopicClick, user }) {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState(
    user?.onboarding_complete ? 'for-you' : 'all'
  );
  const [refreshing, setRefreshing] = useState(false);

  const loadFeed = async (category) => {
    setLoading(true);
    try {
      if (category === 'for-you') {
        const data = await api.getPersonalizedFeed();
        setTopics(data.topics || []);
      } else {
        const data = await api.getFeed(category === 'all' ? undefined : category);
        setTopics(data.topics || []);
      }
    } catch (e) {
      console.error('Feed load failed:', e);
      // Fallback to regular feed if personalized fails
      if (category === 'for-you') {
        try {
          const data = await api.getFeed();
          setTopics(data.topics || []);
        } catch (e2) { console.error('Fallback failed:', e2); }
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFeed(activeCategory);
  }, [activeCategory]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await api.refreshTrending();
      await new Promise(r => setTimeout(r, 2000));
      await loadFeed(activeCategory);
    } catch (e) {
      console.error('Refresh failed:', e);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div data-testid="trending-feed" className="px-5 pt-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center gap-2 mb-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
            bg-red-50 border border-red-100">
            <span className="w-2 h-2 rounded-full bg-red-500 pulse-dot" />
            <span className="text-[10px] font-bold tracking-widest text-red-600 uppercase">
              Live · Confusion Index
            </span>
          </span>
        </div>
        <h1 className="text-3xl font-extrabold text-gray-900 leading-tight">
          WTF is<br />happening?
        </h1>
        <p className="text-sm text-gray-400 mt-2 max-w-[280px]">
          Trending topics explained in 3 cards. No noise, just signal.
        </p>
      </motion.div>

      {/* Category pills */}
      <div className="flex gap-2 mb-5 overflow-x-auto pb-1 scrollbar-hide">
        {CATEGORIES.map(cat => (
          <button
            key={cat.key}
            data-testid={`category-${cat.key}`}
            onClick={() => setActiveCategory(cat.key)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap
              transition-all duration-200 flex items-center gap-1
              ${activeCategory === cat.key
                ? cat.key === 'for-you'
                  ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-sm'
                  : 'bg-gray-900 text-white shadow-sm'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
          >
            {cat.key === 'for-you' && <Sparkles size={11} />}
            {cat.label}
          </button>
        ))}
        <button
          data-testid="refresh-feed-btn"
          onClick={handleRefresh}
          disabled={refreshing}
          className="px-3 py-1.5 rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200
            transition-all duration-200 flex items-center gap-1"
        >
          <RefreshCw size={12} className={refreshing ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Topic cards */}
      <div className="space-y-3">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="shimmer rounded-2xl h-[88px]" />
          ))
        ) : topics.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <p className="text-lg font-medium">No topics yet</p>
            <p className="text-sm mt-1">Pull to refresh or check back soon</p>
          </div>
        ) : (
          <AnimatePresence>
            {topics.map((topic, i) => (
              <TopicCard
                key={topic.id}
                topic={topic}
                index={i}
                onClick={onTopicClick}
              />
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
