import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, ArrowLeft, Check, Search, MapPin, Briefcase, Sparkles, Loader2 } from 'lucide-react';
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
  'Global News', 'Politics', 'Science', 'Business',
  'Internet Culture', 'Sports', 'Climate', 'Space', 'Health',
];

const CURIOSITY_TYPES = [
  'Why markets move',
  'Why countries fight',
  'Why companies succeed or fail',
  'Why technology changes fast',
  'Why things go viral online',
  'Why the economy changes',
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

const SUGGESTED_TOPICS = [
  'AI', 'Tesla', 'Apple', 'Bitcoin', 'OpenAI', 'China',
  'NASA', 'Google', 'Meta', 'Amazon', 'SpaceX', 'Nvidia',
];

const COUNTRIES = [
  'United States', 'United Kingdom', 'Canada', 'Australia', 'Germany',
  'France', 'India', 'Japan', 'Brazil', 'Mexico', 'South Korea',
  'Singapore', 'Netherlands', 'Sweden', 'Switzerland', 'Spain',
  'Italy', 'Ireland', 'Israel', 'UAE', 'South Africa', 'Nigeria',
  'Kenya', 'Other',
];

export default function OnboardingFlow({ user, onComplete }) {
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

  const filteredSuggested = SUGGESTED_TOPICS.filter(t =>
    !topicSearch || t.toLowerCase().includes(topicSearch.toLowerCase())
  );

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
              <div className="text-center pt-16">
                <motion.div
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ type: 'spring', stiffness: 200, delay: 0.1 }}
                  className="w-20 h-20 rounded-3xl bg-gray-900 text-white flex items-center justify-center
                    mx-auto mb-6 text-3xl font-black"
                >
                  W
                </motion.div>
                <h1 className="text-2xl font-extrabold text-gray-900 leading-snug mb-3">
                  Understand what's<br />happening in the world<br />in 30 seconds
                </h1>
                <p className="text-sm text-gray-400 max-w-[280px] mx-auto mb-2">
                  We explain trending topics with 3 simple cards.
                  No noise, just clarity.
                </p>
                <p className="text-sm text-gray-400">
                  Let's personalize your feed.
                </p>
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
                    placeholder="Search topics or companies"
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-white border border-gray-200
                      text-sm text-gray-900 placeholder:text-gray-400 outline-none
                      focus:border-gray-400 focus:shadow-sm transition-all"
                  />
                </div>
                <div className="flex flex-wrap gap-2">
                  {filteredSuggested.map(topic => (
                    <button
                      key={topic}
                      data-testid={`follow-${topic.toLowerCase()}`}
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
                {followedTopics.length > 0 && (
                  <p className="text-xs text-gray-400 mt-3">
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
