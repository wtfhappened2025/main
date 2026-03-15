import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Sparkles, Loader2 } from 'lucide-react';
import api from '@/api';

export default function ExplainInput({ onExplained }) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    setLoading(true);
    setError('');
    try {
      const data = await api.explain(input.trim());
      if (onExplained) {
        onExplained(data.topic, data.explanation);
      }
      setInput('');
    } catch (e) {
      console.error('Explain failed:', e);
      setError('Something went wrong. Try again.');
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    "Why is gold at an all-time high?",
    "What's happening with AI regulation?",
    "Why did the stock market crash?",
    "What is quantum computing?",
  ];

  return (
    <div data-testid="explain-input" className="px-5 pt-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center gap-2 mb-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
            bg-teal-50 border border-teal-100">
            <Sparkles size={10} className="text-teal-600" />
            <span className="text-[10px] font-bold tracking-widest text-teal-600 uppercase">
              AI-Powered
            </span>
          </span>
        </div>
        <h1 className="text-3xl font-extrabold text-gray-900 leading-tight">
          Paste anything.<br />Get clarity.
        </h1>
      </motion.div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="relative mb-6">
        <div className="flex items-center bg-white rounded-2xl border border-gray-200 
          shadow-sm px-4 py-3 focus-within:border-gray-400 focus-within:shadow-md
          transition-all duration-200">
          <Search size={18} className="text-gray-400 mr-3 flex-shrink-0" />
          <input
            data-testid="explain-input-field"
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Paste a headline or question..."
            className="flex-1 bg-transparent outline-none text-sm text-gray-900 
              placeholder:text-gray-400"
            disabled={loading}
          />
          <button
            data-testid="explain-submit-btn"
            type="submit"
            disabled={!input.trim() || loading}
            className={`ml-2 w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0
              transition-all duration-200
              ${input.trim() && !loading
                ? 'bg-gray-900 text-white hover:bg-gray-800'
                : 'bg-gray-100 text-gray-400'}`}
          >
            {loading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Sparkles size={16} />
            )}
          </button>
        </div>
      </form>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="text-red-500 text-sm text-center mb-4"
            data-testid="explain-error"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>

      {/* Loading state */}
      <AnimatePresence>
        {loading && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-white rounded-2xl border border-gray-100 p-8 text-center mb-6"
          >
            <div className="w-12 h-12 rounded-full bg-gray-900 text-white flex items-center justify-center mx-auto mb-4">
              <Sparkles size={20} className="animate-pulse" />
            </div>
            <p className="text-sm font-semibold text-gray-900">Generating explanation...</p>
            <p className="text-xs text-gray-400 mt-1">AI is analyzing your topic</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Suggestions */}
      {!loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <p className="text-center text-sm text-gray-400 mb-4">
            Drop a confusing headline.<br />Get 3 cards of clarity.
          </p>
          <div className="space-y-2 mt-6">
            <p className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-2">
              Try these
            </p>
            {suggestions.map((s, i) => (
              <motion.button
                key={i}
                data-testid={`suggestion-${i}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.08 }}
                onClick={() => setInput(s)}
                className="w-full text-left px-4 py-3 rounded-xl bg-white border border-gray-100
                  text-sm text-gray-600 hover:bg-gray-50 hover:border-gray-200
                  transition-all duration-150"
              >
                {s}
              </motion.button>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
