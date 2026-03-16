import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, MessageCircle, TrendingUp, Zap, RefreshCw } from 'lucide-react';
import api from '@/api';

const LOGO_URL = 'https://customer-assets.emergentagent.com/job_web-pulse-4/artifacts/0qv7i1f2_WTFH%20logo.png';

const CATEGORIES = [
  { key: 'for-you', label: 'YOUR NEWS', emoji: '✨', color: '#8B5CF6', bg: '#7C3AED', activeBg: 'linear-gradient(135deg, #8B5CF6, #6D28D9)' },
  { key: 'all', label: 'ALL', emoji: '🌍', color: '#6B7280', bg: '#F3F4F6', activeBg: '#111827' },
  { key: 'finance', label: 'MARKETS', emoji: '📈', color: '#059669', bg: '#ECFDF5', activeBg: '#059669' },
  { key: 'technology', label: 'TECH', emoji: '⚡', color: '#2563EB', bg: '#EFF6FF', activeBg: '#2563EB' },
  { key: 'economy', label: 'ECONOMY', emoji: '💰', color: '#D97706', bg: '#FFFBEB', activeBg: '#D97706' },
  { key: 'crypto', label: 'CRYPTO', emoji: '🪙', color: '#EA580C', bg: '#FFF7ED', activeBg: '#EA580C' },
  { key: 'ai', label: 'AI', emoji: '🤖', color: '#7C3AED', bg: '#F5F3FF', activeBg: '#7C3AED' },
  { key: 'science', label: 'SCIENCE', emoji: '🔬', color: '#7C3AED', bg: '#EDE9FE', activeBg: '#7C3AED' },
  { key: 'entertainment', label: 'CELEB', emoji: '🎬', color: '#DB2777', bg: '#FDF2F8', activeBg: '#DB2777' },
  { key: 'lifestyle', label: 'STYLE', emoji: '✨', color: '#9333EA', bg: '#FAF5FF', activeBg: '#9333EA' },
];

const CARD_THEMES = {
  finance:      { bg: '#EBF5FF', accent: '#3B82F6', bgEmoji: '📊', text: '#1E3A5F' },
  technology:   { bg: '#FCEEF1', accent: '#E11D48', bgEmoji: '⚡', text: '#4A1525' },
  ai:           { bg: '#ECFDF5', accent: '#10B981', bgEmoji: '🧠', text: '#14532D' },
  economy:      { bg: '#FFF8E1', accent: '#F59E0B', bgEmoji: '💲', text: '#78350F' },
  crypto:       { bg: '#FFF7ED', accent: '#F97316', bgEmoji: '₿', text: '#7C2D12' },
  science:      { bg: '#EDE9FE', accent: '#8B5CF6', bgEmoji: '🔬', text: '#4C1D95' },
  world_news:   { bg: '#FEF2F2', accent: '#EF4444', bgEmoji: '🌎', text: '#7F1D1D' },
  internet_culture: { bg: '#FFF1F2', accent: '#F43F5E', bgEmoji: '🌐', text: '#881337' },
  politics:     { bg: '#FEF2F2', accent: '#DC2626', bgEmoji: '🏛️', text: '#991B1B' },
  entertainment:{ bg: '#FDF2F8', accent: '#EC4899', bgEmoji: '⭐', text: '#831843' },
  lifestyle:    { bg: '#F5F3FF', accent: '#A855F7', bgEmoji: '✨', text: '#581C87' },
};

const CAT_EMOJI = {
  finance: '📈', technology: '⚡', ai: '🤖', economy: '💰', crypto: '🪙',
  science: '🔬', world_news: '🌍', internet_culture: '🌐', politics: '🏛️',
  entertainment: '🎬', lifestyle: '✨',
};

function Sparkline({ score, color }) {
  const bars = Array.from({ length: 7 }, (_, i) => {
    const h = 6 + Math.floor(Math.random() * 18) + (i > 4 ? score / 10 : 0);
    return h;
  });
  return (
    <div className="flex items-end gap-[2px] h-5">
      {bars.map((h, i) => (
        <div key={i} style={{ width: 3, height: h, background: color, opacity: 0.5 + (i / 10), borderRadius: 1 }} />
      ))}
    </div>
  );
}

function TiltCard({ children, className, style, onClick, testId }) {
  const ref = useRef(null);
  const handleMove = (e) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    el.style.transform = `perspective(800px) rotateY(${x * 8}deg) rotateX(${-y * 8}deg) scale(1.02)`;
  };
  const handleLeave = () => {
    if (ref.current) ref.current.style.transform = 'perspective(800px) rotateY(0) rotateX(0) scale(1)';
  };
  return (
    <div
      ref={ref}
      data-testid={testId}
      onClick={onClick}
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      className={className}
      style={{ ...style, transition: 'transform 0.2s ease-out', transformStyle: 'preserve-3d', cursor: 'pointer' }}
    >
      {children}
    </div>
  );
}

function MosaicCard({ topic, isHero, onClick }) {
  const theme = CARD_THEMES[topic.category] || CARD_THEMES.world_news;
  const views = Math.floor(8000 + topic.trend_score * 80 + Math.random() * 2000);
  const comments = Math.floor(views * 0.025 + Math.random() * 50);
  const fmtNum = (n) => n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n;

  return (
    <TiltCard
      testId={`topic-card-${topic.id}`}
      onClick={() => onClick(topic)}
      className={`relative overflow-hidden rounded-2xl p-4 ${isHero ? 'col-span-2' : ''}`}
      style={{ background: theme.bg }}
    >
      {/* Giant background emoji */}
      <div className="absolute pointer-events-none select-none" style={{
        fontSize: isHero ? 160 : 100,
        right: isHero ? -10 : -15,
        bottom: isHero ? -20 : -25,
        opacity: 0.09,
        lineHeight: 1,
      }}>
        {theme.bgEmoji}
      </div>

      {/* Header: category + time + score */}
      <div className="flex items-center justify-between mb-2 relative z-10">
        <div className="flex items-center gap-1.5">
          <span className="text-sm">{CAT_EMOJI[topic.category] || '📰'}</span>
          <span className="text-[10px] font-extrabold tracking-widest uppercase" style={{ color: theme.accent }}>
            {CATEGORIES.find(c => c.key === topic.category)?.label || topic.category}
          </span>
          <span className="text-[10px] text-gray-400 ml-1">{topic.time_ago}</span>
        </div>
        {/* Trend score badge */}
        <div className="flex items-center gap-1 px-2 py-1 rounded-full" style={{ background: `${theme.accent}18` }}>
          <span className="text-xs">🔥</span>
          <span className="text-xs font-bold" style={{ color: theme.accent }}>{topic.trend_score}</span>
        </div>
      </div>

      {/* Title */}
      <h3
        className={`font-extrabold leading-tight relative z-10 ${isHero ? 'text-2xl mb-3' : 'text-base mb-2'}`}
        style={{ color: theme.text }}
      >
        {topic.title}
      </h3>

      {/* Hero card: show description */}
      {isHero && topic.has_explanation && (
        <p className="text-sm leading-relaxed mb-3 relative z-10 line-clamp-3" style={{ color: `${theme.text}BB` }}>
          {topic.title.length < 40
            ? 'Tap to see what happened, why it matters, and how it affects you — explained in 3 simple cards.'
            : 'Breaking down the key facts, the deeper reasons, and what it means for you personally.'}
        </p>
      )}

      {/* Footer: views, comments, sparkline */}
      <div className="flex items-center gap-3 mt-auto relative z-10 pt-2">
        <div className="flex items-center gap-1 text-gray-400">
          <Eye size={12} />
          <span className="text-[11px] font-medium">{fmtNum(views)}</span>
        </div>
        <div className="flex items-center gap-1 text-gray-400">
          <MessageCircle size={12} />
          <span className="text-[11px] font-medium">{fmtNum(comments)}</span>
        </div>
        {isHero && (
          <div className="flex items-center gap-1 text-gray-400 ml-1">
            <TrendingUp size={12} />
          </div>
        )}
        <div className="ml-auto">
          <Sparkline score={topic.trend_score} color={theme.accent} />
        </div>
      </div>
    </TiltCard>
  );
}

export default function TrendingFeed({ onTopicClick, user }) {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState(
    user?.onboarding_complete ? 'for-you' : 'all'
  );
  const [refreshing, setRefreshing] = useState(false);
  const [counts, setCounts] = useState({});

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
      if (category === 'for-you') {
        try { const data = await api.getFeed(); setTopics(data.topics || []); } catch (e2) { /* noop */ }
      }
    } finally { setLoading(false); }
  };

  useEffect(() => { loadFeed(activeCategory); }, [activeCategory]);

  // Load category counts once
  useEffect(() => {
    (async () => {
      try {
        const data = await api.getFeed('all');
        const c = {};
        (data.topics || []).forEach(t => { c[t.category] = (c[t.category] || 0) + 1; });
        setCounts(c);
      } catch {}
    })();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadFeed(activeCategory);
    setRefreshing(false);
  };

  const totalTopics = Object.values(counts).reduce((a, b) => a + b, 0);

  return (
    <div data-testid="trending-feed" className="pb-24">
      {/* Header */}
      <div className="mb-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <img src={LOGO_URL} alt="WTFHappened" className="h-7 object-contain" />
          </div>
          <motion.div
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-50 border border-red-100"
          >
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-[10px] font-bold text-red-500 tracking-wider">LIVE</span>
          </motion.div>
        </div>

        <h1 className="text-3xl sm:text-4xl font-black text-gray-900 leading-none mb-1">
          WTF is<br />happening?
        </h1>
        <span className="text-4xl">🌍</span>
        <p className="text-sm text-gray-400 mt-2 mb-3">
          Trending topics explained in 3 cards. No noise, just signal.
        </p>

        {/* Live stat badges */}
        <div className="flex items-center gap-2 mb-4">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-green-50 border border-green-100">
            <TrendingUp size={13} className="text-green-600" />
            <span className="text-xs font-bold text-green-700">{totalTopics || '...'}</span>
            <span className="text-[10px] text-green-600">trending</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-orange-50 border border-orange-100">
            <Zap size={13} className="text-orange-500" />
            <span className="text-xs font-bold text-orange-700">42k</span>
            <span className="text-[10px] text-orange-500">reading</span>
          </div>
          <button
            data-testid="feed-refresh"
            onClick={handleRefresh}
            disabled={refreshing}
            className="ml-auto p-2 rounded-full hover:bg-gray-100 transition-colors"
          >
            <RefreshCw size={16} className={`text-gray-400 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Category filter pills */}
      <div className="flex gap-2 mb-5 overflow-x-auto pb-1.5 scrollbar-hide -mx-1 px-1">
        {CATEGORIES.map(cat => {
          const isActive = activeCategory === cat.key;
          const count = cat.key === 'for-you' ? (topics.length || '') :
                        cat.key === 'all' ? '' : (counts[cat.key] || '');
          return (
            <motion.button
              key={cat.key}
              data-testid={`category-${cat.key}`}
              onClick={() => setActiveCategory(cat.key)}
              whileTap={{ scale: 0.95 }}
              className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-bold whitespace-nowrap transition-colors"
              style={isActive ? {
                background: cat.activeBg,
                color: '#fff',
                boxShadow: `0 4px 14px ${cat.color}40`,
              } : {
                background: cat.bg,
                color: cat.color,
                border: `1px solid ${cat.color}20`,
              }}
            >
              <span className="text-sm">{cat.emoji}</span>
              {cat.label}
              {isActive && count ? (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="ml-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-bold"
                  style={{ background: 'rgba(255,255,255,0.3)' }}
                >
                  {count}
                </motion.span>
              ) : null}
            </motion.button>
          );
        })}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div
            key="loader"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex justify-center py-16"
          >
            <div className="w-8 h-8 rounded-full border-2 border-gray-200 border-t-gray-900 animate-spin" />
          </motion.div>
        ) : topics.length === 0 ? (
          <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-16">
            <p className="text-gray-400 text-sm">No topics found for this category</p>
          </motion.div>
        ) : (
          <motion.div
            key={activeCategory}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.25 }}
            className="grid grid-cols-2 gap-3"
            data-testid="mosaic-grid"
          >
            {topics.slice(0, 20).map((topic, i) => (
              <MosaicCard
                key={topic.id}
                topic={topic}
                isHero={i === 0}
                onClick={onTopicClick}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
