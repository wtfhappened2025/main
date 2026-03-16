import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const LOGO_URL = 'https://customer-assets.emergentagent.com/job_web-pulse-4/artifacts/0qv7i1f2_WTFH%20logo.png';

const FLOATING_EMOJIS = [
  { emoji: '\uD83D\uDD25', x: '10%', y: '5%', size: 32, delay: 0 },
  { emoji: '\uD83D\uDE31', x: '80%', y: '8%', size: 28, delay: 0.5 },
  { emoji: '\uD83E\uDD2F', x: '65%', y: '3%', size: 36, delay: 1 },
  { emoji: '\uD83D\uDC80', x: '25%', y: '12%', size: 24, delay: 1.5 },
  { emoji: '\uD83D\uDCC8', x: '90%', y: '20%', size: 30, delay: 0.3 },
  { emoji: '\u26A1', x: '5%', y: '25%', size: 26, delay: 0.8 },
  { emoji: '\uD83D\uDE80', x: '75%', y: '72%', size: 34, delay: 1.2 },
  { emoji: '\uD83D\uDC40', x: '15%', y: '78%', size: 28, delay: 0.6 },
  { emoji: '\uD83D\uDCB0', x: '85%', y: '80%', size: 32, delay: 1.8 },
  { emoji: '\uD83E\uDD16', x: '50%', y: '85%', size: 30, delay: 0.4 },
  { emoji: '\uD83C\uDFDB\uFE0F', x: '35%', y: '90%', size: 24, delay: 1.1 },
  { emoji: '\uD83C\uDF0D', x: '60%', y: '75%', size: 28, delay: 0.9 },
];

const MINI_TAGS = [
  { emoji: '\uD83D\uDD25', text: 'Markets crashed', bg: '#FEF3C7', color: '#92400E' },
  { emoji: '\uD83E\uDD16', text: 'AI update', bg: '#FFF8E1', color: '#78350F' },
  { emoji: '\uD83D\uDC80', text: 'No way', bg: '#FCE7F3', color: '#9D174D' },
];

export default function SplashScreen({ onContinue }) {
  const [liveCount, setLiveCount] = useState(2847);

  useEffect(() => {
    const interval = setInterval(() => {
      setLiveCount(prev => prev + Math.floor(Math.random() * 3));
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      data-testid="splash-screen"
      className="fixed inset-0 overflow-hidden flex flex-col items-center justify-center cursor-pointer"
      style={{
        background: 'linear-gradient(160deg, #f5f0ff 0%, #fdf2f8 30%, #fff7ed 60%, #fef3c7 100%)',
      }}
      onClick={onContinue}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.05 }}
      transition={{ duration: 0.4 }}
    >
      {/* Floating emojis */}
      {FLOATING_EMOJIS.map((item, i) => (
        <motion.div
          key={i}
          className="absolute select-none pointer-events-none"
          style={{ left: item.x, top: item.y, fontSize: item.size }}
          initial={{ opacity: 0, scale: 0 }}
          animate={{
            opacity: [0, 0.3, 0.15, 0.3],
            scale: [0, 1, 0.9, 1],
            y: [0, -12, 0, -12],
            rotate: [0, 5, -5, 0],
          }}
          transition={{
            duration: 5,
            delay: item.delay,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        >
          {item.emoji}
        </motion.div>
      ))}

      {/* Logo */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.6 }}
        className="mb-6 z-10"
      >
        <img src={LOGO_URL} alt="WTFHappened" className="h-10 object-contain" />
      </motion.div>

      {/* Main card */}
      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ delay: 0.4, duration: 0.6, type: 'spring', stiffness: 100 }}
        className="bg-white/90 backdrop-blur-lg rounded-3xl shadow-xl p-8 max-w-sm w-[90%] text-center z-10"
      >
        <h1 className="text-3xl sm:text-4xl font-black text-gray-800 leading-tight mb-3">
          News just got<br />unhinged.
        </h1>
        <p className="text-sm text-gray-500 mb-1">
          Swipe through today's chaos. React with
        </p>
        <p className="text-lg mb-1">{'\uD83D\uDD25\uD83E\uDD2F\uD83D\uDE31'}</p>
        <p className="text-sm text-gray-500 mb-5">
          Get the vibe, skip the boring parts.
        </p>

        {/* Mini topic tags */}
        <div className="flex items-center justify-center gap-2">
          {MINI_TAGS.map((tag, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 + i * 0.15 }}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold"
              style={{ background: tag.bg, color: tag.color }}
            >
              <span>{tag.emoji}</span>
              <span>{tag.text}</span>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* CTA button */}
      <motion.button
        data-testid="splash-cta"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 0.5 }}
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        onClick={(e) => { e.stopPropagation(); onContinue(); }}
        className="mt-8 px-10 py-4 rounded-full text-white font-bold text-base z-10 shadow-lg"
        style={{
          background: 'linear-gradient(135deg, #8B5CF6, #7C3AED)',
          boxShadow: '0 8px 30px rgba(124, 58, 237, 0.35)',
        }}
      >
        WTF is happening? {'\u2192'}
      </motion.button>

      {/* Tap hint */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
        className="mt-5 text-[10px] tracking-[0.2em] uppercase text-gray-400 font-bold z-10"
      >
        tap anywhere for {'\u2728'} vibes {'\u2728'}
      </motion.p>

      {/* Live counter */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
        className="mt-3 flex items-center gap-2 px-4 py-2 rounded-full bg-white/60 backdrop-blur-sm z-10"
      >
        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
        <span className="text-xs text-gray-600">
          <strong className="text-gray-800">{liveCount.toLocaleString()}</strong> people catching up rn
        </span>
      </motion.div>
    </motion.div>
  );
}
