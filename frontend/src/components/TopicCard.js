import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Flame, TrendingUp, ChevronRight } from 'lucide-react';

const CATEGORY_CONFIG = {
  finance: { label: 'MARKETS', icon: '📈', color: '#3B82F6' },
  technology: { label: 'TECH', icon: '⚡', color: '#10B981' },
  ai: { label: 'AI', icon: '🤖', color: '#6B7280' },
  economy: { label: 'ECONOMY', icon: '💰', color: '#F59E0B' },
  crypto: { label: 'CRYPTO', icon: '🪙', color: '#F97316' },
  science: { label: 'SCIENCE', icon: '🔬', color: '#8B5CF6' },
  world_news: { label: 'WORLD', icon: '🌍', color: '#EF4444' },
  internet_culture: { label: 'CULTURE', icon: '🌐', color: '#F43F5E' },
  politics: { label: 'POLITICS', icon: '🏛️', color: '#DC2626' },
  entertainment: { label: 'CELEB', icon: '🎬', color: '#EC4899' },
  lifestyle: { label: 'STYLE', icon: '✨', color: '#A855F7' },
};

export default function TopicCard({ topic, index, onClick }) {
  const cat = CATEGORY_CONFIG[topic.category] || CATEGORY_CONFIG.world_news;
  const isHot = topic.trend_score >= 85;

  return (
    <motion.div
      data-testid={`topic-card-${index}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.35 }}
      onClick={() => onClick(topic)}
      className={`cat-${topic.category} rounded-2xl p-4 cursor-pointer
        hover:scale-[1.01] active:scale-[0.99] transition-transform duration-150`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm">{cat.icon}</span>
          <span
            className="text-[10px] font-bold tracking-widest uppercase"
            style={{ color: cat.color }}
          >
            {cat.label}
          </span>
          <span className="text-[10px] text-gray-400">
            · {topic.time_ago || 'recently'}
          </span>
        </div>
        <div className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold
          ${isHot ? 'bg-red-50 text-red-600 score-hot' : 'bg-gray-50 text-gray-600'}`}>
          {isHot && <span className="w-1.5 h-1.5 rounded-full bg-red-500 pulse-dot" />}
          <Flame size={12} className={isHot ? 'text-orange-500' : 'text-gray-400'} />
          <span>{topic.trend_score}</span>
        </div>
      </div>
      <h3 className="text-base font-semibold text-gray-900 leading-snug pr-4">
        {topic.title}
      </h3>
    </motion.div>
  );
}
