import { motion } from 'framer-motion';
import { Flame, Search, Bookmark } from 'lucide-react';

const TABS = [
  { key: 'home', label: 'HOME', Icon: Flame },
  { key: 'explain', label: 'EXPLAIN', Icon: Search },
  { key: 'saved', label: 'SAVED', Icon: Bookmark },
];

export default function BottomNav({ activeTab, onTabChange }) {
  return (
    <div className="bottom-nav" data-testid="bottom-nav">
      <div className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-lg border border-gray-100
        flex items-center justify-around py-2 px-2">
        {TABS.map(tab => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              data-testid={`nav-${tab.key}`}
              onClick={() => onTabChange(tab.key)}
              className={`relative flex flex-col items-center gap-0.5 px-6 py-2 rounded-xl
                transition-all duration-200
                ${isActive ? 'bg-gray-100' : 'hover:bg-gray-50'}`}
            >
              <tab.Icon
                size={20}
                className={`transition-colors duration-200
                  ${isActive ? 'text-gray-900' : 'text-gray-400'}`}
                fill={isActive ? 'currentColor' : 'none'}
              />
              <span className={`text-[9px] font-bold uppercase tracking-[0.12em]
                transition-colors duration-200
                ${isActive ? 'text-gray-900' : 'text-gray-400'}`}>
                {tab.label}
              </span>
              {isActive && (
                <motion.div
                  layoutId="nav-indicator"
                  className="absolute -bottom-0.5 left-1/2 -translate-x-1/2 w-6 h-0.5 
                    rounded-full bg-gray-900"
                />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
