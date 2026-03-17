import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, ArrowLeft, Check, Search, MapPin, Briefcase, Sparkles, Loader2, Plus } from 'lucide-react';
import api from '@/api';

const STEPS = [
  { key: 'welcome', title: 'Welcome' },
  { key: 'interests', title: 'Interests' },
  { key: 'curiosity', title: 'Curiosity' },
  { key: 'depth', title: 'Depth' },
  { key: 'location', title: 'Location' },
  { key: 'professional', title: 'Context' },
  { key: 'follow', title: 'Follow' },
];

const INTERESTS = [
  'Technology', 'AI', 'Startups', 'Finance', 'Crypto',
  'Business', 'Global News', 'Politics', 'Science', 'Space',
  'Health', 'Psychology', 'Internet Culture', 'Memes',
  'Viral Trends', 'Celebrities', 'Movies & TV', 'Music',
  'Fashion', 'Gaming', 'Sports', 'Travel', 'Food',
  'Strange News', 'Future Tech',
];

const CURIOSITY_TYPES = [
  'Why markets move',
  'Why companies succeed or fail',
  'Why technology changes so fast',
  'Why countries fight',
  'Why the economy changes',
  'Why things go viral online',
  'Why memes explode',
  'Why celebrities trend',
  'Why influencers get famous',
  'Why startups suddenly explode',
  'Why society trends change',
  'Why people believe strange things',
  'Why random weird things happen',
  'Why internet stories spread',
];

const DEPTH_OPTIONS = [
  { key: 'simple', label: 'Simple', desc: '30 second explanation', icon: '⚡' },
  { key: 'moderate', label: 'Moderate', desc: 'With context', icon: '📖' },
  { key: 'deep', label: 'Deep', desc: 'Data and analysis', icon: '🔬' },
];

const PROFESSIONAL_OPTIONS = [
  'Student', 'Tech professional', 'Investor / trader',
  'Founder / entrepreneur', 'General curious person',
];

const TOPIC_GROUPS = [
  { label: 'Technology', topics: ['AI', 'Nvidia', 'Apple', 'Google'] },
  { label: 'Finance', topics: ['Bitcoin', 'Stock Market', 'Venture Capital'] },
  { label: 'Countries', topics: ['China', 'USA', 'Russia'] },
  { label: 'Internet', topics: ['TikTok', 'Memes', 'Influencers'] },
];

const ALL_SUGGESTED = TOPIC_GROUPS.flatMap(g => [g.label, ...g.topics]);

const COUNTRIES = [
  'United States', 'United Kingdom', 'Canada', 'Australia', 'Germany',
  'France', 'India', 'Japan', 'Brazil', 'Mexico', 'South Korea',
  'Singapore', 'Netherlands', 'Sweden', 'Switzerland', 'Spain',
  'Italy', 'Ireland', 'Israel', 'UAE', 'South Africa', 'Nigeria',
  'Kenya', 'Other',
];

const LOGO_URL = 'https://customer-assets.emergentagent.com/job_web-pulse-4/artifacts/0qv7i1f2_WTFH%20logo.png';

export default function OnboardingFlow({ user, onComplete, onLogout }) {
  const [step, setStep] = useState(0);
  const [interests, setInterests] = useState([]);
  const [curiosityTypes, setCuriosityTypes] = useState([]);
  const [depth, setDepth] = useState('simple');
  const [country, setCountry] = useState('');
  const [region, setRegion] = useState('');
  const [professional, setProfessional] = useState('');
  const [followedTopics, setFollowedTopics] = useState([]);
  const [topicSearch, setTopicSearch] = useState('');
  const [saving, setSaving] = useState(false);

  const toggleItem = (list, setList, item) => {
    setList(prev => prev.includes(item) ? prev.filter(i => i !== item) : [...prev, item]);
  };

  const canProceed = () => {
    if (step === 0) return true; // welcome
    if (step === 1) return interests.length > 0;
    if (step === 2) return curiosityTypes.length > 0;
    if (step === 3) return !!depth;
    if (step === 4) return !!country;
    if (step === 5) return true; // optional
    if (step === 6) return true; // optional
    return true;
  };

  const handleFinish = async () => {
    setSaving(true);
    try {
      await api.saveOnboarding({
        interests,
        curiosity_types: curiosityTypes,
        explanation_depth: depth,
        country,
        region,
        professional_context: professional,
        followed_topics: followedTopics,
      });
      const updatedUser = { ...user, onboarding_complete: true, preferences: {
        interests, curiosity_types: curiosityTypes, explanation_depth: depth,
        country, region, professional_context: professional, followed_topics: followedTopics,
      }};
      localStorage.setItem('wtf_user', JSON.stringify(updatedUser));
      onComplete(updatedUser);
    } catch (e) {
      console.error('Onboarding save failed:', e);
      // Still proceed
      onComplete({ ...user, onboarding_complete: true });
    } finally {
      setSaving(false);
    }
  };

  const handleNext = () => {
    if (step === STEPS.length - 1) {
      handleFinish();
    } else {
      setStep(s => s + 1);
    }
  };

  const searchMatchesExisting = topicSearch.trim() &&
    ALL_SUGGESTED.some(t => t.toLowerCase() === topicSearch.trim().toLowerCase());
  const searchMatchesFollowed = topicSearch.trim() &&
    followedTopics.some(t => t.toLowerCase() === topicSearch.trim().toLowerCase());
  const canAddCustom = topicSearch.trim().length >= 2 && !searchMatchesExisting && !searchMatchesFollowed;

  const handleAddCustomTopic = () => {
    const custom = topicSearch.trim();
    if (custom && !followedTopics.includes(custom)) {
      setFollowedTopics(prev => [...prev, custom]);
    }
    setTopicSearch('');
  };

  const progress = ((step + 1) / STEPS.length) * 100;

  return (
    <div data-testid="onboarding-flow" className="min-h-screen flex flex-col px-5 py-6">
      {/* Progress bar */}
      {step > 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <button
              data-testid="onboarding-back"
              onClick={() => setStep(s => s - 1)}
              className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center
                hover:bg-gray-200 transition-colors"
            >
              <ArrowLeft size={16} className="text-gray-600" />
            </button>
            <span className="text-[10px] font-bold text-gray-400 tracking-widest uppercase">
              {step} / {STEPS.length - 1}
            </span>
          </div>
          <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gray-900 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>
      )}

      {/* Welcome step: back/logout button */}
      {step === 0 && (
        <div className="flex justify-end">
          <button
            data-testid="onboarding-logout"
            onClick={onLogout}
            className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          >
            Sign Out
          </button>
        </div>
      )}

      {/* Step content */}
      <div className="flex-1">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            transition={{ duration: 0.25 }}
          >
            {/* Step 0: Welcome */}
            {step === 0 && (
              <div className="flex flex-col items-center justify-center min-h-[70vh] text-center">
                <motion.img
                  src={LOGO_URL}
                  alt="WTFHappened"
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ type: 'spring', stiffness: 200, delay: 0.1 }}
                  className="h-24 sm:h-28 mx-auto mb-8 object-contain"
                />
                <h1 className="text-4xl sm:text-5xl font-black text-gray-900 leading-[1.1] mb-5">
                  Understand what's<br />happening in the world<br />in 30 seconds
                </h1>
                <p className="text-lg text-gray-400 max-w-[340px] mx-auto mb-3 leading-relaxed">
                  We explain trending topics with 3 simple cards.
                  No noise, just clarity.
                </p>
                <p className="text-lg text-gray-400">
                  Let's personalize your feed.
                </p>

                {/* Visual feature pills */}
                <div className="flex flex-wrap justify-center gap-3 mt-8 max-w-md">
                  {[
                    { emoji: '\u26A1', text: '3-card explainers' },
                    { emoji: '\uD83D\uDD25', text: 'Trending topics' },
                    { emoji: '\uD83E\uDD16', text: 'AI-powered' },
                  ].map((item, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.4 + i * 0.15 }}
                      className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-white border border-gray-100 shadow-sm"
                    >
                      <span className="text-xl">{item.emoji}</span>
                      <span className="text-sm font-semibold text-gray-700">{item.text}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Step 1: Interests */}
            {step === 1 && (
              <div>
                <h2 className="text-xl font-extrabold text-gray-900 mb-1">Pick your interests</h2>
                <p className="text-sm text-gray-400 mb-5">Select topics you care about. Choose at least one.</p>
                <div className="flex flex-wrap gap-2">
                  {INTERESTS.map(item => (
                    <button
                      key={item}
                      data-testid={`interest-${item.toLowerCase().replace(/\s/g, '-')}`}
                      onClick={() => toggleItem(interests, setInterests, item)}
                      className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-150
                        ${interests.includes(item)
                          ? 'bg-gray-900 text-white shadow-sm'
                          : 'bg-white border border-gray-200 text-gray-600 hover:border-gray-300'}`}
                    >
                      {interests.includes(item) && <Check size={14} className="inline mr-1" />}
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Step 2: Curiosity Type */}
            {step === 2 && (
              <div>
                <h2 className="text-xl font-extrabold text-gray-900 mb-1">What are you curious about?</h2>
                <p className="text-sm text-gray-400 mb-5">This helps us pick better explanations for you.</p>
                <div className="space-y-2">
                  {CURIOSITY_TYPES.map(item => (
                    <button
                      key={item}
                      data-testid={`curiosity-${item.toLowerCase().replace(/\s/g, '-').replace(/[^a-z0-9-]/g, '')}`}
                      onClick={() => toggleItem(curiosityTypes, setCuriosityTypes, item)}
                      className={`w-full text-left px-4 py-3.5 rounded-xl text-sm font-medium
                        transition-all duration-150 flex items-center justify-between
                        ${curiosityTypes.includes(item)
                          ? 'bg-gray-900 text-white'
                          : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-300'}`}
                    >
                      <span>{item}</span>
                      {curiosityTypes.includes(item) && <Check size={16} />}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Step 3: Explanation Depth */}
            {step === 3 && (
              <div>
                <h2 className="text-xl font-extrabold text-gray-900 mb-1">How detailed?</h2>
                <p className="text-sm text-gray-400 mb-5">Set your preferred explanation depth.</p>
                <div className="space-y-3">
                  {DEPTH_OPTIONS.map(opt => (
                    <button
                      key={opt.key}
                      data-testid={`depth-${opt.key}`}
                      onClick={() => setDepth(opt.key)}
                      className={`w-full text-left px-5 py-4 rounded-2xl transition-all duration-150
                        flex items-center gap-4
                        ${depth === opt.key
                          ? 'bg-gray-900 text-white shadow-md'
                          : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-300'}`}
                    >
                      <span className="text-2xl">{opt.icon}</span>
                      <div>
                        <p className="font-semibold">{opt.label}</p>
                        <p className={`text-xs mt-0.5 ${depth === opt.key ? 'text-gray-300' : 'text-gray-400'}`}>
                          {opt.desc}
                        </p>
                      </div>
                      {depth === opt.key && (
                        <Check size={18} className="ml-auto" />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Step 4: Location */}
            {step === 4 && (
              <div>
                <h2 className="text-xl font-extrabold text-gray-900 mb-1">Where are you?</h2>
                <p className="text-sm text-gray-400 mb-5">We'll show you regionally relevant trends.</p>
                <div className="space-y-3">
                  <div className="relative">
                    <MapPin size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                    <select
                      data-testid="location-country"
                      value={country}
                      onChange={e => setCountry(e.target.value)}
                      className="w-full pl-10 pr-4 py-3 rounded-xl bg-white border border-gray-200
                        text-sm text-gray-900 outline-none focus:border-gray-400
                        focus:shadow-sm transition-all appearance-none"
                    >
                      <option value="">Select country</option>
                      {COUNTRIES.map(c => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                  <input
                    data-testid="location-region"
                    type="text"
                    value={region}
                    onChange={e => setRegion(e.target.value)}
                    placeholder="Region or city (optional)"
                    className="w-full px-4 py-3 rounded-xl bg-white border border-gray-200
                      text-sm text-gray-900 placeholder:text-gray-400 outline-none
                      focus:border-gray-400 focus:shadow-sm transition-all"
                  />
                </div>
              </div>
            )}

            {/* Step 5: Professional Context */}
            {step === 5 && (
              <div>
                <h2 className="text-xl font-extrabold text-gray-900 mb-1">What describes you best?</h2>
                <p className="text-sm text-gray-400 mb-1">This is optional but improves relevance.</p>
                <p className="text-xs text-gray-300 mb-5">
                  <Briefcase size={12} className="inline mr-1" />
                  You can skip this step
                </p>
                <div className="space-y-2">
                  {PROFESSIONAL_OPTIONS.map(opt => (
                    <button
                      key={opt}
                      data-testid={`professional-${opt.toLowerCase().replace(/[\s\/]/g, '-')}`}
                      onClick={() => setProfessional(professional === opt ? '' : opt)}
                      className={`w-full text-left px-4 py-3.5 rounded-xl text-sm font-medium
                        transition-all duration-150 flex items-center justify-between
                        ${professional === opt
                          ? 'bg-gray-900 text-white'
                          : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-300'}`}
                    >
                      <span>{opt}</span>
                      {professional === opt && <Check size={16} />}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Step 6: Follow Topics */}
            {step === 6 && (
              <div>
                <h2 className="text-xl font-extrabold text-gray-900 mb-1">Follow specific topics</h2>
                <p className="text-sm text-gray-400 mb-5">Get notified when these trend.</p>
                <div className="relative mb-4">
                  <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    data-testid="topic-search"
                    type="text"
                    value={topicSearch}
                    onChange={e => setTopicSearch(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter' && canAddCustom) { e.preventDefault(); handleAddCustomTopic(); } }}
                    placeholder="Search or type to add your own"
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-white border border-gray-200
                      text-sm text-gray-900 placeholder:text-gray-400 outline-none
                      focus:border-gray-400 focus:shadow-sm transition-all"
                  />
                </div>

                {canAddCustom && (
                  <button
                    data-testid="add-custom-topic"
                    onClick={handleAddCustomTopic}
                    className="w-full mb-4 px-4 py-2.5 rounded-xl bg-blue-50 text-blue-700 text-sm font-medium
                      flex items-center gap-2 hover:bg-blue-100 transition-colors border border-blue-100"
                  >
                    <Plus size={14} /> Add "{topicSearch.trim()}"
                  </button>
                )}

                {/* Custom added topics (not in groups) */}
                {followedTopics.filter(t => !ALL_SUGGESTED.includes(t)).length > 0 && (
                  <div className="mb-4">
                    <p className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-2">Your Topics</p>
                    <div className="flex flex-wrap gap-2">
                      {followedTopics.filter(t => !ALL_SUGGESTED.includes(t)).map(topic => (
                        <button
                          key={topic}
                          data-testid={`follow-custom-${topic.toLowerCase().replace(/\s/g, '-')}`}
                          onClick={() => toggleItem(followedTopics, setFollowedTopics, topic)}
                          className="px-4 py-2.5 rounded-xl text-sm font-medium bg-gray-900 text-white shadow-sm transition-all duration-150"
                        >
                          <Check size={14} className="inline mr-1" />{topic}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Grouped suggested topics */}
                <div className="space-y-4">
                  {TOPIC_GROUPS.map(group => (
                    <div key={group.label}>
                      <p className="text-[10px] font-bold text-gray-400 tracking-widest uppercase mb-2">{group.label}</p>
                      <div className="flex flex-wrap gap-2">
                        {group.topics.map(topic => (
                          <button
                            key={topic}
                            data-testid={`follow-${topic.toLowerCase().replace(/\s/g, '-')}`}
                            onClick={() => toggleItem(followedTopics, setFollowedTopics, topic)}
                            className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-150
                              ${followedTopics.includes(topic)
                                ? 'bg-gray-900 text-white shadow-sm'
                                : 'bg-white border border-gray-200 text-gray-600 hover:border-gray-300'}`}
                          >
                            {followedTopics.includes(topic) && <Check size={14} className="inline mr-1" />}
                            {topic}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                {followedTopics.length > 0 && (
                  <p className="text-xs text-gray-400 mt-4">
                    Following {followedTopics.length} topic{followedTopics.length > 1 ? 's' : ''}
                  </p>
                )}
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Bottom action */}
      <div className="mt-8 pb-4">
        <button
          data-testid="onboarding-next"
          onClick={handleNext}
          disabled={!canProceed() || saving}
          className={`w-full py-3.5 rounded-xl text-sm font-semibold flex items-center justify-center gap-2
            transition-all duration-200
            ${canProceed() && !saving
              ? 'bg-gray-900 text-white hover:bg-gray-800'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'}`}
        >
          {saving ? (
            <Loader2 size={18} className="animate-spin" />
          ) : step === 0 ? (
            <>Get Started <Sparkles size={16} /></>
          ) : step === STEPS.length - 1 ? (
            <>Finish Setup <Check size={16} /></>
          ) : (
            <>Continue <ArrowRight size={16} /></>
          )}
        </button>
        {step > 0 && step < STEPS.length - 1 && step >= 5 && (
          <button
            data-testid="onboarding-skip"
            onClick={handleNext}
            className="w-full py-2 mt-2 text-xs text-gray-400 hover:text-gray-600 transition-colors"
          >
            Skip this step
          </button>
        )}
      </div>
    </div>
  );
}
