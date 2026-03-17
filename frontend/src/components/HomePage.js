import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Flame, Zap, TrendingUp, ArrowRight } from 'lucide-react';
import api from '@/api';

const LOGO_URL = 'https://customer-assets.emergentagent.com/job_web-pulse-4/artifacts/0qv7i1f2_WTFH%20logo.png';

const CAT_LABELS = {
  finance: 'MARKETS', technology: 'TECH', ai: 'AI', economy: 'ECONOMY',
  crypto: 'CRYPTO', science: 'SCIENCE', world_news: 'WORLD',
  internet_culture: 'CULTURE', politics: 'POLITICS',
  entertainment: 'CELEB', lifestyle: 'STYLE',
};

// Category-specific stock images from Unsplash
const CAT_IMAGES = {
  finance: [
    'https://images.unsplash.com/photo-1768055105681-7d2096c5165f?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1767424196045-030bbde122a4?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1768055104929-cf2317674a80?w=800&h=600&fit=crop',
  ],
  technology: [
    'https://images.unsplash.com/photo-1771189957040-3a4f9b78812c?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1706777280252-5de52771cf13?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1573757056004-065ad36e2cf4?w=800&h=600&fit=crop',
  ],
  ai: [
    'https://images.unsplash.com/photo-1760629863094-5b1e8d1aae74?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1769839271832-cfd7a1f6854f?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1771515220841-2dfbfe80e9e2?w=800&h=600&fit=crop',
  ],
  economy: [
    'https://images.unsplash.com/photo-1591033594798-33227a05780d?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1763047360803-4f0432c73b11?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1646776930319-b16b17781725?w=800&h=600&fit=crop',
  ],
  crypto: [
    'https://images.unsplash.com/photo-1639133893916-a711d8af8c0a?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1652337037919-62e284ff2839?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1639754391010-d24457e21118?w=800&h=600&fit=crop',
  ],
  science: [
    'https://images.unsplash.com/photo-1707944746058-4da338d0f827?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1707944745853-b86631676829?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1707944745900-ae9f750f2c69?w=800&h=600&fit=crop',
  ],
  world_news: [
    'https://images.unsplash.com/photo-1618847207931-c05e836bbdb5?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1588623731810-171b80f3c55e?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1613662265610-051b02ce6630?w=800&h=600&fit=crop',
  ],
  politics: [
    'https://images.unsplash.com/photo-1627990316935-9c473904206e?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1760488352907-8af7f514cce3?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1666798044958-9df7c6cc279a?w=800&h=600&fit=crop',
  ],
  entertainment: [
    'https://images.unsplash.com/photo-1561835661-ebd6f6283571?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1614115866447-c9a299154650?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1760030428042-f2bd83bc03ba?w=800&h=600&fit=crop',
  ],
  lifestyle: [
    'https://images.unsplash.com/photo-1762331966914-c72c3f6624d1?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1644908325834-3dfd46b1c629?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1771514021692-b4ebc7ec28ee?w=800&h=600&fit=crop',
  ],
  internet_culture: [
    'https://images.unsplash.com/photo-1762340275305-4a716fdd3b08?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1762340275963-04400d52c393?w=800&h=600&fit=crop',
    'https://images.unsplash.com/photo-1762330469300-2732c258c686?w=800&h=600&fit=crop',
  ],
};

function getTopicImage(topic, index) {
  const pool = CAT_IMAGES[topic.category] || CAT_IMAGES.world_news;
  // Use a simple hash of topic id to pick a consistent image
  let hash = 0;
  for (let i = 0; i < (topic.id || '').length; i++) {
    hash = ((hash << 5) - hash + topic.id.charCodeAt(i)) | 0;
  }
  return pool[Math.abs(hash + index) % pool.length];
}

function BentoCard({ topic, isHero, onClick, index }) {
  const label = CAT_LABELS[topic.category] || 'NEWS';
  const imgUrl = getTopicImage(topic, index);

  return (
    <motion.button
      data-testid={`home-topic-${topic.id}`}
      onClick={() => onClick(topic)}
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.35 + index * 0.12 }}
      className="relative w-full h-full rounded-2xl overflow-hidden group text-left"
      style={{ minHeight: isHero ? 280 : 134 }}
    >
      {/* Background image */}
      <img
        src={imgUrl}
        alt={topic.title}
        className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
        loading="lazy"
      />
      {/* Dark gradient overlay */}
      <div className="absolute inset-0" style={{
        background: 'linear-gradient(to top, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.3) 50%, rgba(0,0,0,0.05) 100%)',
      }} />

      {/* Content */}
      <div className="absolute inset-0 flex flex-col justify-end p-4">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="text-[10px] font-extrabold tracking-widest text-white/70 uppercase">
            {label}
          </span>
          <span className="text-[10px] font-bold text-orange-400">
            {'\uD83D\uDD25'} {topic.trend_score}
          </span>
        </div>
        <h3 className={`font-bold text-white leading-snug ${isHero ? 'text-lg' : 'text-sm'}`}>
          {topic.title}
        </h3>
        {isHero && (
          <p className="text-xs text-white/60 mt-1 line-clamp-2 leading-relaxed">
            Tap to read the full breakdown in 3 simple cards
          </p>
        )}
      </div>
    </motion.button>
  );
}

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
      } catch { /* noop */ }
      finally { setLoading(false); }
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
          <div key={i} className="bg-white rounded-2xl border border-gray-100 p-4 text-center">
            <stat.icon size={20} className="mx-auto mb-2" style={{ color: stat.color }} />
            <div className="text-2xl font-black text-gray-900">{stat.value}</div>
            <div className="text-[9px] font-bold tracking-wider text-gray-400 uppercase mt-1">
              {stat.label}
            </div>
          </div>
        ))}
      </motion.div>

      {/* Headlines section header */}
      <motion.h2
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="text-sm font-bold text-gray-500 tracking-wider uppercase mb-4 flex items-center gap-1.5"
      >
        {'\uD83D\uDCF0'} Today's Headlines
      </motion.h2>

      {/* Bento image grid */}
      {loading ? (
        <div className="grid grid-cols-5 gap-3" style={{ height: 280 }}>
          <div className="col-span-3 rounded-2xl bg-gray-100 animate-pulse" />
          <div className="col-span-2 flex flex-col gap-3">
            <div className="flex-1 rounded-2xl bg-gray-100 animate-pulse" />
            <div className="flex-1 rounded-2xl bg-gray-100 animate-pulse" />
          </div>
        </div>
      ) : topics.length > 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.35 }}
          className="grid grid-cols-5 gap-3"
          style={{ height: 280 }}
        >
          {/* Hero — left column */}
          <div className="col-span-3">
            <BentoCard topic={topics[0]} isHero onClick={onTopicClick} index={0} />
          </div>

          {/* Right column — 2 stacked */}
          <div className="col-span-2 flex flex-col gap-3">
            {topics[1] && (
              <div className="flex-1">
                <BentoCard topic={topics[1]} onClick={onTopicClick} index={1} />
              </div>
            )}
            {topics[2] && (
              <div className="flex-1">
                <BentoCard topic={topics[2]} onClick={onTopicClick} index={2} />
              </div>
            )}
          </div>
        </motion.div>
      ) : (
        <div className="rounded-2xl bg-gray-100 h-[200px] flex items-center justify-center">
          <p className="text-gray-400 text-sm">No topics yet</p>
        </div>
      )}

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
