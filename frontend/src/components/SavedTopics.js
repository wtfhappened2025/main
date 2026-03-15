import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bookmark, Trash2 } from 'lucide-react';
import api from '@/api';

export default function SavedTopics({ onTopicClick }) {
  const [saved, setSaved] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSaved();
  }, []);

  const loadSaved = async () => {
    setLoading(true);
    try {
      const data = await api.getSaved();
      setSaved(data.saved || []);
    } catch (e) {
      console.error('Failed to load saved:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleUnsave = async (topicId) => {
    try {
      await api.saveTopic(topicId);
      setSaved(prev => prev.filter(s => s.topic?.id !== topicId));
    } catch (e) {
      console.error('Unsave failed:', e);
    }
  };

  return (
    <div data-testid="saved-topics" className="px-5 pt-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center gap-2 mb-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
            bg-emerald-50 border border-emerald-100">
            <Bookmark size={10} className="text-emerald-600" />
            <span className="text-[10px] font-bold tracking-widest text-emerald-600 uppercase">
              Library
            </span>
          </span>
        </div>
        <h1 className="text-3xl font-extrabold text-gray-900 leading-tight">
          Your saved stacks.
        </h1>
      </motion.div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="shimmer rounded-2xl h-24" />
          ))}
        </div>
      ) : saved.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center py-20"
        >
          <div className="w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center mx-auto mb-4">
            <Bookmark size={24} className="text-emerald-400" />
          </div>
          <p className="font-semibold text-gray-900">No saved stacks yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Tap the bookmark on any topic to save it here.
          </p>
        </motion.div>
      ) : (
        <div className="space-y-3">
          <AnimatePresence>
            {saved.map((item, i) => {
              const topic = item.topic;
              if (!topic) return null;
              return (
                <motion.div
                  key={topic.id}
                  data-testid={`saved-item-${i}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                  transition={{ delay: i * 0.05 }}
                  className="bg-white rounded-2xl border border-gray-100 p-4
                    flex items-center justify-between cursor-pointer
                    hover:shadow-sm transition-all duration-150"
                >
                  <div
                    className="flex-1 mr-3"
                    onClick={() => onTopicClick(topic)}
                  >
                    <p className="text-[10px] font-bold tracking-widest text-gray-400 uppercase mb-1">
                      {topic.category?.replace('_', ' ')}
                    </p>
                    <p className="text-sm font-semibold text-gray-900 leading-snug">
                      {topic.title}
                    </p>
                    {item.explanation && (
                      <p className="text-xs text-gray-400 mt-1 line-clamp-1">
                        {item.explanation.card_1}
                      </p>
                    )}
                  </div>
                  <button
                    data-testid={`unsave-btn-${i}`}
                    onClick={(e) => { e.stopPropagation(); handleUnsave(topic.id); }}
                    className="w-8 h-8 rounded-full bg-red-50 flex items-center justify-center
                      text-red-400 hover:bg-red-100 hover:text-red-600 transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
