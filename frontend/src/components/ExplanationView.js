import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Share2, Bookmark, ChevronDown } from 'lucide-react';
import api from '@/api';

const CARD_TABS = [
  { key: 'what', label: 'WHAT', className: 'exp-card-what' },
  { key: 'why', label: 'WHY', className: 'exp-card-why' },
  { key: 'matters', label: 'YOU', className: 'exp-card-matters' },
];

const CARD_LABELS = {
  what: 'WHAT HAPPENED',
  why: 'WHY IT HAPPENED',
  matters: 'WHY IT MATTERS TO YOU',
};

const LABEL_COLORS = {
  what: { bg: '#DBEAFE', text: '#2563EB', dot: '#FBBF24' },
  why: { bg: '#FEF3C7', text: '#D97706', dot: '#F97316' },
  matters: { bg: '#D1FAE5', text: '#059669', dot: '#10B981' },
};

const CATEGORY_CONFIG = {
  finance: { label: 'MARKETS', color: '#3B82F6' },
  technology: { label: 'TECH', color: '#10B981' },
  ai: { label: 'AI', color: '#6B7280' },
  economy: { label: 'ECONOMY', color: '#F59E0B' },
  crypto: { label: 'CRYPTO', color: '#F97316' },
  science: { label: 'SCIENCE', color: '#8B5CF6' },
  world_news: { label: 'WORLD', color: '#EF4444' },
  internet_culture: { label: 'CULTURE', color: '#F43F5E' },
  politics: { label: 'POLITICS', color: '#DC2626' },
};

export default function ExplanationView({ topic, onBack, onShare }) {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('what');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadExplanation();
  }, [topic.id]);

  const loadExplanation = async () => {
    setLoading(true);
    try {
      const data = await api.getExplanation(topic.id);
      setExplanation(data.explanation);
    } catch (e) {
      console.error('Explanation load failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const result = await api.saveTopic(topic.id);
      setSaved(result.saved);
    } catch (e) {
      console.error('Save failed:', e);
    }
  };

  const handleShare = () => {
    if (onShare) onShare(topic);
  };

  const cat = CATEGORY_CONFIG[topic.category] || CATEGORY_CONFIG.world_news;
  const isHot = topic.trend_score >= 85;

  const cardContent = explanation ? {
    what: { main: explanation.card_1, detail: explanation.card_1_detail },
    why: { main: explanation.card_2, detail: explanation.card_2_detail },
    matters: { main: explanation.card_3, detail: explanation.card_3_detail },
  } : {};

  const colors = LABEL_COLORS[activeTab];

  return (
    <div data-testid="explanation-view" className="min-h-screen">
      {/* Header bar */}
      <div className="px-5 pt-5 pb-3" style={{ background: `linear-gradient(180deg, ${cat.color}15 0%, transparent 100%)` }}>
        <div className="flex items-center justify-between mb-3">
          <button
            data-testid="back-button"
            onClick={onBack}
            className="w-9 h-9 rounded-full bg-white/80 backdrop-blur flex items-center justify-center
              hover:bg-white transition-colors"
          >
            <ArrowLeft size={18} className="text-gray-700" />
          </button>
          <div className="flex items-center gap-2">
            <button
              data-testid="save-button"
              onClick={handleSave}
              className={`w-9 h-9 rounded-full flex items-center justify-center transition-colors
                ${saved ? 'bg-yellow-100 text-yellow-600' : 'bg-white/80 backdrop-blur text-gray-700 hover:bg-white'}`}
            >
              <Bookmark size={18} fill={saved ? 'currentColor' : 'none'} />
            </button>
            <button
              data-testid="share-button"
              onClick={handleShare}
              className="w-9 h-9 rounded-full bg-white/80 backdrop-blur flex items-center justify-center
                hover:bg-white transition-colors"
            >
              <Share2 size={18} className="text-gray-700" />
            </button>
          </div>
        </div>

        {/* Topic info */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[10px] font-bold tracking-widest uppercase" style={{ color: cat.color }}>
            {cat.label}
          </span>
          <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold
            ${isHot ? 'bg-red-50 text-red-600' : 'bg-gray-100 text-gray-500'}`}>
            {isHot && <span className="w-1.5 h-1.5 rounded-full bg-red-500 pulse-dot" />}
            <span>🔥 {topic.trend_score}</span>
          </div>
        </div>
        <h2 className="text-xl font-bold text-gray-900 leading-snug">{topic.title}</h2>
      </div>

      {/* Card tabs */}
      <div className="flex justify-center gap-1 px-5 py-3">
        {CARD_TABS.map(tab => (
          <button
            key={tab.key}
            data-testid={`tab-${tab.key}`}
            onClick={() => setActiveTab(tab.key)}
            className={`px-5 py-2 rounded-full text-xs font-bold tracking-wider transition-all duration-200
              ${activeTab === tab.key
                ? 'bg-gray-900 text-white shadow-md'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Explanation card */}
      <div className="px-5 mt-1">
        {loading ? (
          <div className="shimmer rounded-3xl h-[380px]" />
        ) : explanation ? (
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -30 }}
              transition={{ duration: 0.25 }}
              className={`${CARD_TABS.find(t => t.key === activeTab)?.className} 
                rounded-3xl p-6 min-h-[340px] flex flex-col justify-between
                border border-white/50 shadow-sm`}
            >
              <div>
                <span
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold tracking-wider mb-5"
                  style={{ background: `${colors.bg}`, color: colors.text }}
                >
                  <span className="w-2 h-2 rounded-full" style={{ background: colors.dot }} />
                  {CARD_LABELS[activeTab]}
                </span>
                <p className="text-2xl font-bold text-gray-900 leading-snug">
                  {cardContent[activeTab]?.main}
                </p>
              </div>
              <p className="text-sm text-gray-500 leading-relaxed mt-6">
                {cardContent[activeTab]?.detail}
              </p>
            </motion.div>
          </AnimatePresence>
        ) : (
          <div className="rounded-3xl bg-gray-100 h-[340px] flex items-center justify-center">
            <p className="text-gray-400">Failed to load explanation</p>
          </div>
        )}
      </div>

      {/* Progress dots */}
      <div className="flex flex-col items-center mt-5 gap-2">
        <div className="flex gap-2">
          {CARD_TABS.map(tab => (
            <div
              key={tab.key}
              className={`h-1.5 rounded-full transition-all duration-300
                ${activeTab === tab.key ? 'w-8 bg-gray-900' : 'w-3 bg-gray-300'}`}
            />
          ))}
        </div>
        <span className="text-[10px] text-gray-400 tracking-wider uppercase flex items-center gap-1">
          Swipe to navigate <ChevronDown size={10} />
        </span>
      </div>
    </div>
  );
}
