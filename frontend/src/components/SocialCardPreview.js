import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Download, Copy, Check } from 'lucide-react';

const CATEGORY_COLORS = {
  technology: { bg: '#EBF5FF', accent: '#3B82F6', text: '#1E40AF' },
  finance: { bg: '#F0FDF4', accent: '#22C55E', text: '#166534' },
  economy: { bg: '#FFFBEB', accent: '#F59E0B', text: '#92400E' },
  ai: { bg: '#F3E8FF', accent: '#8B5CF6', text: '#5B21B6' },
  crypto: { bg: '#FFF7ED', accent: '#F97316', text: '#9A3412' },
  science: { bg: '#EDE9FE', accent: '#7C3AED', text: '#4C1D95' },
  world_news: { bg: '#FEF2F2', accent: '#EF4444', text: '#991B1B' },
  internet_culture: { bg: '#FFF1F2', accent: '#F43F5E', text: '#9F1239' },
  politics: { bg: '#FEF2F2', accent: '#DC2626', text: '#991B1B' },
};

const TEMPLATES = [
  { key: 'standard', label: 'Square', size: '1080 x 1080', aspect: '1/1' },
  { key: 'twitter', label: 'Twitter', size: '1200 x 675', aspect: '1200/675' },
  { key: 'story', label: 'Story', size: '1080 x 1920', aspect: '9/16' },
];

export default function SocialCardPreview({ cardData, onClose }) {
  const [template, setTemplate] = useState('standard');
  const [copied, setCopied] = useState(false);

  if (!cardData) return null;

  const colors = CATEGORY_COLORS[cardData.category] || CATEGORY_COLORS.world_news;
  const currentTemplate = TEMPLATES.find(t => t.key === template);

  const handleCopyCaption = () => {
    const text = `${cardData.caption}\n\n1. ${cardData.card_1}\n2. ${cardData.card_2}\n3. ${cardData.card_3}\n\n${(cardData.hashtags || []).map(h => `#${h}`).join(' ')}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      data-testid="social-card-preview"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        onClick={e => e.stopPropagation()}
        className="bg-white rounded-3xl max-w-md w-full max-h-[90vh] overflow-y-auto p-5"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold">Social Card</h3>
          <button
            data-testid="close-social-card"
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center
              hover:bg-gray-200 transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Template selector */}
        <div className="flex gap-2 mb-4">
          {TEMPLATES.map(t => (
            <button
              key={t.key}
              data-testid={`template-${t.key}`}
              onClick={() => setTemplate(t.key)}
              className={`flex-1 py-2 rounded-xl text-xs font-semibold transition-all
                ${template === t.key
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Card preview */}
        <div className="flex justify-center mb-4">
          <div
            className="rounded-2xl overflow-hidden shadow-lg"
            style={{
              aspectRatio: currentTemplate.aspect,
              width: template === 'story' ? '200px' : template === 'twitter' ? '320px' : '280px',
              background: colors.bg,
            }}
          >
            <div className="p-6 h-full flex flex-col justify-between">
              <div>
                <p className="text-[10px] font-bold tracking-widest uppercase mb-3"
                  style={{ color: colors.accent }}>
                  {cardData.category?.replace('_', ' ')}
                </p>
                <p className="font-bold text-gray-900 leading-snug mb-4"
                  style={{ fontSize: template === 'story' ? '14px' : '16px' }}>
                  {cardData.title}
                </p>
                <div className="space-y-2">
                  {[cardData.card_1, cardData.card_2, cardData.card_3].map((card, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <span className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white"
                        style={{ background: colors.accent }}>
                        {i + 1}
                      </span>
                      <p className="text-xs text-gray-700 leading-snug">{card}</p>
                    </div>
                  ))}
                </div>
              </div>
              <p className="text-[9px] text-gray-400 mt-3">wtfhappened.app</p>
            </div>
          </div>
        </div>

        {/* Caption */}
        <div className="bg-gray-50 rounded-xl p-3 mb-4">
          <p className="text-xs text-gray-600 mb-2">{cardData.caption}</p>
          <p className="text-[10px] text-gray-400">
            {(cardData.hashtags || []).map(h => `#${h}`).join(' ')}
          </p>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <button
            data-testid="copy-caption-btn"
            onClick={handleCopyCaption}
            className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl
              bg-gray-900 text-white text-sm font-semibold hover:bg-gray-800 transition-colors"
          >
            {copied ? <Check size={16} /> : <Copy size={16} />}
            {copied ? 'Copied!' : 'Copy Caption'}
          </button>
        </div>

        <p className="text-[10px] text-center text-gray-400 mt-3">
          {currentTemplate.size} · {currentTemplate.label} format
        </p>
      </motion.div>
    </motion.div>
  );
}
