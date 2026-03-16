import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Flame, Zap, TrendingUp, ArrowRight, ChevronRight } from 'lucide-react';
import api from '@/api';

const LOGO_URL = 'https://customer-assets.emergentagent.com/job_web-pulse-4/artifacts/0qv7i1f2_WTFH%20logo.png';

const CAT_STYLES = {
  finance:      { emoji: '\uD83D\uDCC8', label: 'MARKETS', bg: '#FEF2F2', iconBg: '#FECACA', color: '#991B1B' },
  technology:   { emoji: '\u26A1', label: 'TECH', bg: '#FEF9C3', iconBg: '#FEF08A', color: '#854D0E' },
  ai:           { emoji: '\uD83E\uDD16', label: 'AI', bg: '#ECFDF5', iconBg: '#A7F3D0', color: '#065F46' },
  economy:      { emoji: '\uD83D\uDCB0', label: 'ECONOMY', bg: '#FFF7ED', iconBg: '#FED7AA', color: '#9A3412' },
  crypto:       { emoji: '\uD83E\uDE99', label: 'CRYPTO', bg: '#FFF7ED', iconBg: '#FDBA74', color: '#C2410C' },
  science:      { emoji: '\uD83D\uDD2C', label: 'SCIENCE', bg: '#EDE9FE', iconBg: '#C4B5FD', color: '#5B21B6' },
  world_news:   { emoji: '\uD83C\uDF0D', label: 'WORLD', bg: '#FEF2F2', iconBg: '#FECACA', color: '#991B1B' },
  internet_culture: { emoji: '\uD83C\uDF10', label: 'CULTURE', bg: '#FFF1F2', iconBg: '#FECDD3', color: '#9F1239' },
  politics:     { emoji: '\uD83C\uDFDB\uFE0F', label: 'POLITICS', bg: '#FEF2F2', iconBg: '#FECACA', color: '#DC2626' },
  entertainment:{ emoji: '\uD83C\uDFAC', label: 'CELEB', bg: '#FDF2F8', iconBg: '#FBCFE8', color: '#9D174D' },
  lifestyle:    { emoji: '\u2728', label: 'STYLE', bg: '#F5F3FF', iconBg: '#DDD6FE', color: '#6D28D9' },
};

export default function HomePage({ onBrowseAll, onTopicClick, user }) {
  const [topics, setTopics] = useState([]);
  const [stats, setStats] = useState({ topics: 0, confused: 0, read: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const data = user?.onboarding_complete
          ? await api.getPersonalizedFeed()
          : await api.getFeed();
        const allTopics = data.topics || [];
        setTopics(allTopics.slice(0, 3));
        setStats({
          topics: allTopics.length,
          confused: Math.floor(8000 + allTopics.length * 200 + Math.random() * 4000),
          read: Math.floor(5000 + allTopics.length * 150 + Math.random() * 3000),
        });
      } catch {
        /* noop */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const fmtNum = (n) => n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n;

  const STAT_CARDS = [
    { icon: Flame, value: stats.topics, label: 'TOPICS TRENDING', color: '#F97316' },
    { icon: Zap, value: fmtNum(stats.confused), label: 'PEOPLE CONFUSED', color: '#EAB308' },
    { icon: TrendingUp, value: fmtNum(stats.read), label: 'EXPLANATIONS READ', color: '#8B5CF6' },
  ];

  return (
    <div data-testid="home-page" className="pb-24">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <img src={LOGO_URL} alt="WTFHappened" className="h-7 object-contain mb-4" />
        <h1 className="text-3xl font-black text-gray-900 leading-tight">
          Hey there {'\uD83D\uDC4B'}
        </h1>
        <p className="text-base text-gray-500 mt-1">
          Here's what's blowing up right now
        </p>
      </motion.div>

      {/* Stats row */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="grid grid-cols-3 gap-3 mb-8"
      >
        {STAT_CARDS.map((stat, i) => (
          <div
            key={i}
            className="bg-white rounded-2xl border border-gray-100 p-4 text-center"
          >
            <stat.icon size={20} className="mx-auto mb-2" style={{ color: stat.color }} />
            <div className="text-2xl font-black text-gray-900">{stat.value}</div>
            <div className="text-[9px] font-bold tracking-wider text-gray-400 uppercase mt-1">
              {stat.label}
            </div>
          </div>
        ))}
      </motion.div>

      {/* Top 3 section */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="text-sm font-bold text-gray-500 tracking-wider uppercase mb-4 flex items-center gap-1.5">
          {'\uD83D\uDD25'} Top 3 Right Now
        </h2>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-20 rounded-2xl bg-gray-100 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {topics.map((topic, i) => {
              const cat = CAT_STYLES[topic.category] || CAT_STYLES.world_news;
              return (
                <motion.button
                  key={topic.id}
                  data-testid={`home-topic-${topic.id}`}
                  onClick={() => onTopicClick(topic)}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 + i * 0.1 }}
                  className="w-full flex items-center gap-3 bg-white rounded-2xl border border-gray-100 p-4
                    hover:shadow-md hover:border-gray-200 transition-all text-left group"
                >
                  {/* Category icon */}
                  <div
                    className="w-12 h-12 rounded-2xl flex items-center justify-center text-xl shrink-0"
                    style={{ background: cat.iconBg }}
                  >
                    {cat.emoji}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-[10px] font-extrabold tracking-widest uppercase text-gray-400">
                        {cat.label}
                      </span>
                      <div className="flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                        <span className="text-[10px] font-bold text-orange-500">
                          {'\uD83D\uDD25'} {topic.trend_score}
                        </span>
                      </div>
                    </div>
                    <h3 className="text-sm font-bold text-gray-900 leading-snug line-clamp-1">
                      {topic.title}
                    </h3>
                    {topic.has_explanation && (
                      <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">
                        Tap to read the explanation in 3 cards
                      </p>
                    )}
                  </div>

                  {/* Arrow */}
                  <div className="w-8 h-8 rounded-full bg-gray-50 flex items-center justify-center shrink-0
                    group-hover:bg-purple-50 transition-colors">
                    <ChevronRight size={16} className="text-gray-400 group-hover:text-purple-500 transition-colors" />
                  </div>
                </motion.button>
              );
            })}
          </div>
        )}
      </motion.div>

      {/* Browse All CTA */}
      <motion.button
        data-testid="browse-all-topics"
        onClick={onBrowseAll}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.98 }}
        className="w-full mt-6 py-4 rounded-2xl text-white font-bold text-base flex items-center justify-center gap-2"
        style={{
          background: 'linear-gradient(135deg, #8B5CF6, #7C3AED)',
          boxShadow: '0 6px 24px rgba(124, 58, 237, 0.3)',
        }}
      >
        Browse All Topics <ArrowRight size={18} />
      </motion.button>

      {/* Hint text */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="text-center text-xs text-gray-400 mt-4"
      >
        Swipe right to save · left to skip {'\uD83D\uDC4B'}
      </motion.p>
    </div>
  );
}
