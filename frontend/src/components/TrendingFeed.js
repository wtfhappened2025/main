import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence, useAnimation } from 'framer-motion';
import { Eye, MessageCircle, TrendingUp, Zap, RefreshCw, Bookmark, Share2, ChevronRight, ArrowLeft } from 'lucide-react';
import api from '@/api';

const LOGO_URL = 'https://customer-assets.emergentagent.com/job_web-pulse-4/artifacts/i5z1wfjq_WTFH%20logo.png';

const CATEGORIES = [
  { key: 'for-you', label: 'YOUR NEWS', emoji: '\u2728', color: '#8B5CF6', bg: '#7C3AED', activeBg: 'linear-gradient(135deg, #8B5CF6, #6D28D9)' },
  { key: 'all', label: 'ALL', emoji: '\uD83C\uDF0D', color: '#6B7280', bg: '#F3F4F6', activeBg: '#111827' },
  { key: 'finance', label: 'MARKETS', emoji: '\uD83D\uDCC8', color: '#059669', bg: '#ECFDF5', activeBg: '#059669' },
  { key: 'technology', label: 'TECH', emoji: '\u26A1', color: '#2563EB', bg: '#EFF6FF', activeBg: '#2563EB' },
  { key: 'economy', label: 'ECONOMY', emoji: '\uD83D\uDCB0', color: '#D97706', bg: '#FFFBEB', activeBg: '#D97706' },
  { key: 'crypto', label: 'CRYPTO', emoji: '\uD83E\uDE99', color: '#EA580C', bg: '#FFF7ED', activeBg: '#EA580C' },
  { key: 'ai', label: 'AI', emoji: '\uD83E\uDD16', color: '#7C3AED', bg: '#F5F3FF', activeBg: '#7C3AED' },
  { key: 'science', label: 'SCIENCE', emoji: '\uD83D\uDD2C', color: '#7C3AED', bg: '#EDE9FE', activeBg: '#7C3AED' },
  { key: 'entertainment', label: 'CELEB', emoji: '\uD83C\uDFAC', color: '#DB2777', bg: '#FDF2F8', activeBg: '#DB2777' },
  { key: 'lifestyle', label: 'STYLE', emoji: '\u2728', color: '#9333EA', bg: '#FAF5FF', activeBg: '#9333EA' },
];

const CARD_THEMES = {
  finance:      { bg: '#EBF5FF', accent: '#3B82F6', bgEmoji: '\uD83D\uDCCA', text: '#1E3A5F', border: '#3B82F620' },
  technology:   { bg: '#FCEEF1', accent: '#E11D48', bgEmoji: '\u26A1', text: '#4A1525', border: '#E11D4820' },
  ai:           { bg: '#ECFDF5', accent: '#10B981', bgEmoji: '\uD83E\uDDE0', text: '#14532D', border: '#10B98120' },
  economy:      { bg: '#FFF8E1', accent: '#F59E0B', bgEmoji: '\uD83D\uDCB2', text: '#78350F', border: '#F59E0B20' },
  crypto:       { bg: '#FFF7ED', accent: '#F97316', bgEmoji: '\u20BF', text: '#7C2D12', border: '#F9731620' },
  science:      { bg: '#EDE9FE', accent: '#8B5CF6', bgEmoji: '\uD83D\uDD2C', text: '#4C1D95', border: '#8B5CF620' },
  world_news:   { bg: '#FEF2F2', accent: '#EF4444', bgEmoji: '\uD83C\uDF0E', text: '#7F1D1D', border: '#EF444420' },
  internet_culture: { bg: '#FFF1F2', accent: '#F43F5E', bgEmoji: '\uD83C\uDF10', text: '#881337', border: '#F43F5E20' },
  politics:     { bg: '#FEF2F2', accent: '#DC2626', bgEmoji: '\uD83C\uDFDB\uFE0F', text: '#991B1B', border: '#DC262620' },
  entertainment:{ bg: '#FDF2F8', accent: '#EC4899', bgEmoji: '\u2B50', text: '#831843', border: '#EC489920' },
  lifestyle:    { bg: '#F5F3FF', accent: '#A855F7', bgEmoji: '\u2728', text: '#581C87', border: '#A855F720' },
};

const CAT_EMOJI = {
  finance: '\uD83D\uDCC8', technology: '\u26A1', ai: '\uD83E\uDD16', economy: '\uD83D\uDCB0', crypto: '\uD83E\uDE99',
  science: '\uD83D\uDD2C', world_news: '\uD83C\uDF0D', internet_culture: '\uD83C\uDF10', politics: '\uD83C\uDFDB\uFE0F',
  entertainment: '\uD83C\uDFAC', lifestyle: '\u2728',
};

const REACTIONS = [
  { key: 'fire', emoji: '\uD83D\uDD25' },
  { key: 'shocked', emoji: '\uD83D\uDE31' },
  { key: 'mindblown', emoji: '\uD83E\uDD2F' },
  { key: 'angry', emoji: '\uD83D\uDE24' },
];

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

function MosaicCard({ topic, isHero, onClick, onDismiss, onSave, onReact, savedIds, userReactions }) {
  const theme = CARD_THEMES[topic.category] || CARD_THEMES.world_news;
  const controls = useAnimation();
  const views = Math.floor(8000 + topic.trend_score * 80 + Math.random() * 2000);
  const comments = Math.floor(views * 0.025 + Math.random() * 50);
  const fmtNum = (n) => n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n;
  const isSaved = savedIds.has(topic.id);
  const myEmojis = userReactions[topic.id] || [];
  const topicReactions = topic.reactions || {};

  const handleDragEnd = async (_, info) => {
    if (Math.abs(info.offset.x) > 120) {
      const dir = info.offset.x > 0 ? 1 : -1;
      await controls.start({ x: dir * 400, opacity: 0, transition: { duration: 0.3 } });
      onDismiss(topic.id);
    } else {
      controls.start({ x: 0, opacity: 1, transition: { type: 'spring', stiffness: 500, damping: 30 } });
    }
  };

  const handleSave = (e) => {
    e.stopPropagation();
    onSave(topic.id);
  };

  const handleReact = (e, emoji) => {
    e.stopPropagation();
    onReact(topic.id, emoji);
  };

  return (
    <motion.div
      data-testid={`topic-card-${topic.id}`}
      animate={controls}
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.4}
      onDragEnd={handleDragEnd}
      whileTap={{ scale: 0.98 }}
      className={`relative overflow-hidden rounded-2xl ${isHero ? 'col-span-2' : ''}`}
      style={{
        background: theme.bg,
        border: `1px solid ${theme.border}`,
        cursor: 'grab',
        touchAction: 'pan-y',
      }}
    >
      <div className="p-4" onClick={() => onClick(topic)}>
        {/* Giant background emoji */}
        <div className="absolute pointer-events-none select-none" style={{
          fontSize: isHero ? 160 : 100,
          right: isHero ? -10 : -15,
          bottom: isHero ? -20 : -25,
          opacity: 0.06,
          lineHeight: 1,
        }}>
          {theme.bgEmoji}
        </div>

        {/* Header: category + time + score + bookmark */}
        <div className="flex items-center justify-between mb-2 relative z-10">
          <div className="flex items-center gap-1.5">
            <span className="text-sm">{CAT_EMOJI[topic.category] || '\uD83D\uDCF0'}</span>
            <span className="text-[10px] font-extrabold tracking-widest uppercase" style={{ color: theme.accent }}>
              {CATEGORIES.find(c => c.key === topic.category)?.label || topic.category}
            </span>
            <span className="text-[10px] text-gray-400 ml-1">{topic.time_ago}</span>
            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full ml-1" style={{ background: `${theme.accent}18` }}>
              <span className="text-[10px]">{'\uD83D\uDD25'}</span>
              <span className="text-[10px] font-bold" style={{ color: theme.accent }}>{topic.trend_score}</span>
            </div>
          </div>
          <button
            data-testid={`save-btn-${topic.id}`}
            onClick={handleSave}
            className="w-7 h-7 rounded-full flex items-center justify-center transition-colors hover:bg-white/50"
          >
            <Bookmark size={15} className={isSaved ? 'text-yellow-500 fill-yellow-500' : 'text-gray-400'} />
          </button>
        </div>

        {/* Title */}
        <h3
          className={`font-extrabold leading-tight relative z-10 ${isHero ? 'text-2xl mb-2' : 'text-base mb-1.5'}`}
          style={{ color: theme.text }}
        >
          {topic.title}
        </h3>

        {/* Hero: description */}
        {isHero && (
          <p className="text-sm leading-relaxed mb-2 relative z-10 line-clamp-2" style={{ color: `${theme.text}99` }}>
            Breaking down the key facts, the deeper reasons, and what it means for you personally.
          </p>
        )}

        {/* Read in 3 cards CTA */}
        {topic.has_explanation && (
          <div className="flex items-center gap-1 mb-3 relative z-10">
            <span className="text-xs font-bold" style={{ color: theme.accent }}>Read in 3 cards</span>
            <ChevronRight size={14} style={{ color: theme.accent }} />
          </div>
        )}

        {/* Stats row */}
        <div className="flex items-center gap-3 relative z-10">
          <div className="flex items-center gap-1 text-gray-400">
            <Eye size={12} />
            <span className="text-[11px] font-medium">{fmtNum(views)}</span>
          </div>
          <div className="flex items-center gap-1 text-gray-400">
            <MessageCircle size={12} />
            <span className="text-[11px] font-medium">{fmtNum(comments)}</span>
          </div>
          <Sparkline score={topic.trend_score} color={theme.accent} />
          {isHero && (
            <button
              data-testid={`share-btn-${topic.id}`}
              onClick={(e) => { e.stopPropagation(); onClick(topic); }}
              className="ml-auto w-7 h-7 rounded-full flex items-center justify-center hover:bg-white/50 transition-colors"
            >
              <Share2 size={14} className="text-gray-400" />
            </button>
          )}
        </div>
      </div>

      {/* Emoji reactions row */}
      <div
        className="flex items-center gap-1.5 px-4 pb-3 pt-1 relative z-10"
        onClick={(e) => e.stopPropagation()}
      >
        {REACTIONS.map(r => {
          const count = Math.max(topicReactions[r.key] || 0, 0);
          const isActive = myEmojis.includes(r.key);
          return (
            <button
              key={r.key}
              data-testid={`react-${r.key}-${topic.id}`}
              onClick={(e) => handleReact(e, r.key)}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold transition-all
                ${isActive
                  ? 'bg-white shadow-sm ring-1 ring-gray-200 scale-105'
                  : 'bg-white/40 hover:bg-white/70'}`}
            >
              <span className="text-sm">{r.emoji}</span>
              {count > 0 && <span className="text-gray-500">{count}</span>}
            </button>
          );
        })}
      </div>
    </motion.div>
  );
}

export default function TrendingFeed({ onTopicClick, user, onBack }) {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState(
    user?.onboarding_complete ? 'for-you' : 'all'
  );
  const [refreshing, setRefreshing] = useState(false);
  const [counts, setCounts] = useState({});
  const [dismissed, setDismissed] = useState(new Set());
  const [savedIds, setSavedIds] = useState(new Set());
  const [userReactions, setUserReactions] = useState({});

  const loadFeed = async (category) => {
    setLoading(true);
    try {
      let data;
      if (category === 'for-you') {
        data = await api.getPersonalizedFeed();
      } else {
        data = await api.getFeed(category === 'all' ? undefined : category);
      }
      setTopics(data.topics || []);

      // Load user's reactions for these topics
      const ids = (data.topics || []).map(t => t.id);
      if (ids.length > 0) {
        try {
          const rxData = await api.getMyReactions(ids);
          setUserReactions(rxData.reactions || {});
        } catch { /* not logged in or error */ }
      }
    } catch (e) {
      if (category === 'for-you') {
        try {
          const data = await api.getFeed();
          setTopics(data.topics || []);
        } catch { /* noop */ }
      }
    } finally { setLoading(false); }
  };

  // Load saved topics
  useEffect(() => {
    (async () => {
      try {
        const data = await api.getSaved();
        const ids = new Set((data.saved || []).map(s => s.topic?.id).filter(Boolean));
        setSavedIds(ids);
      } catch { /* not logged in */ }
    })();
  }, []);

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
    setDismissed(new Set());
    await loadFeed(activeCategory);
    setRefreshing(false);
  };

  const handleDismiss = useCallback((topicId) => {
    setDismissed(prev => new Set([...prev, topicId]));
    api.dismissTopic(topicId).catch(() => {});
  }, []);

  const handleSave = useCallback(async (topicId) => {
    try {
      const res = await api.saveTopic(topicId);
      setSavedIds(prev => {
        const next = new Set(prev);
        if (res.saved) next.add(topicId);
        else next.delete(topicId);
        return next;
      });
    } catch { /* not logged in */ }
  }, []);

  const handleReact = useCallback(async (topicId, emoji) => {
    try {
      const res = await api.reactToTopic(topicId, emoji);
      // Update topic reactions in state
      setTopics(prev => prev.map(t =>
        t.id === topicId ? { ...t, reactions: res.reactions } : t
      ));
      // Update user reactions
      setUserReactions(prev => {
        const cur = [...(prev[topicId] || [])];
        if (res.toggled) {
          if (!cur.includes(emoji)) cur.push(emoji);
        } else {
          const idx = cur.indexOf(emoji);
          if (idx > -1) cur.splice(idx, 1);
        }
        return { ...prev, [topicId]: cur };
      });
    } catch { /* not logged in */ }
  }, []);

  const visibleTopics = topics.filter(t => !dismissed.has(t.id));
  const totalTopics = Object.values(counts).reduce((a, b) => a + b, 0);

  return (
    <div data-testid="trending-feed" className="pb-24">
      {/* Header */}
      <div className="mb-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            {onBack && (
              <button
                data-testid="feed-back-btn"
                onClick={onBack}
                className="w-9 h-9 rounded-full bg-white border border-gray-200 flex items-center justify-center
                  hover:bg-gray-50 transition-colors mr-1"
              >
                <ArrowLeft size={16} className="text-gray-600" />
              </button>
            )}
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
        <span className="text-4xl">{'\uD83C\uDF0D'}</span>
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
        ) : visibleTopics.length === 0 ? (
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
            <AnimatePresence>
              {visibleTopics.slice(0, 20).map((topic, i) => (
                <motion.div
                  key={topic.id}
                  layout
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8, transition: { duration: 0.2 } }}
                  transition={{ delay: i * 0.03 }}
                  className={i === 0 ? 'col-span-2' : ''}
                >
                  <MosaicCard
                    topic={topic}
                    isHero={i === 0}
                    onClick={onTopicClick}
                    onDismiss={handleDismiss}
                    onSave={handleSave}
                    onReact={handleReact}
                    savedIds={savedIds}
                    userReactions={userReactions}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
