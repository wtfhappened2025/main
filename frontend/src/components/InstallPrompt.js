import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, X } from 'lucide-react';

export default function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem('wtf_pwa_dismissed');
    if (dismissed) { setDismissed(true); return; }

    const handler = (e) => { e.preventDefault(); setDeferredPrompt(e); };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const result = await deferredPrompt.userChoice;
    if (result.outcome === 'accepted') setDeferredPrompt(null);
  };

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem('wtf_pwa_dismissed', '1');
  };

  if (!deferredPrompt || dismissed) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 100, opacity: 0 }}
        data-testid="install-prompt"
        className="fixed bottom-20 left-4 right-4 z-50 bg-gray-900 text-white rounded-2xl p-4 shadow-2xl"
      >
        <button
          data-testid="install-dismiss"
          onClick={handleDismiss}
          className="absolute top-3 right-3 p-1 rounded-full hover:bg-gray-700 transition-colors"
        >
          <X size={14} />
        </button>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center flex-shrink-0">
            <Download size={18} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-bold">Install WTFHappened</p>
            <p className="text-[11px] text-gray-400 mt-0.5">Get instant access from your home screen</p>
          </div>
          <button
            data-testid="install-accept"
            onClick={handleInstall}
            className="px-4 py-2 rounded-xl bg-white text-gray-900 text-xs font-bold hover:bg-gray-100 transition-colors flex-shrink-0"
          >
            Install
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
