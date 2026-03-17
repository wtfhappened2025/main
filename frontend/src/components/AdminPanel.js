import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LogOut, Users, FileText, Newspaper, BarChart3, Search,
  Edit3, Trash2, Plus, Save, X, Loader2, ChevronDown, Clock, Send, RefreshCw
} from 'lucide-react';
import api from '@/api';

const ADMIN_TABS = [
  { key: 'overview', label: 'Overview', icon: BarChart3 },
  { key: 'users', label: 'Users', icon: Users },
  { key: 'prompts', label: 'AI Prompts', icon: FileText },
  { key: 'topics', label: 'News Feed', icon: Newspaper },
  { key: 'scheduler', label: 'Scheduler', icon: Clock },
  { key: 'publisher', label: 'Publisher', icon: Send },
];

const CATEGORIES = [
  'technology', 'finance', 'ai', 'economy', 'crypto', 'science', 'world_news', 'internet_culture', 'politics', 'entertainment', 'lifestyle'
];

export default function AdminPanel({ onLogout }) {
  const [tab, setTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [prompts, setPrompts] = useState([]);
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState(null);
  const [editSystemPrompt, setEditSystemPrompt] = useState('');
  const [editTaskPrompt, setEditTaskPrompt] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [showAddTopic, setShowAddTopic] = useState(false);
  const [newTopic, setNewTopic] = useState({ title: '', category: 'technology', trend_score: 50 });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [schedulerData, setSchedulerData] = useState(null);
  const [publishedCards, setPublishedCards] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (tab === 'overview') loadStats();
    if (tab === 'users') loadUsers();
    if (tab === 'prompts') loadPrompts();
    if (tab === 'topics') loadTopics();
    if (tab === 'scheduler') loadScheduler();
    if (tab === 'publisher') loadPublished();
  }, [tab]);

  const loadStats = async () => { try { setStats((await api.adminGetStats())); } catch (e) { console.error(e); } };
  const loadUsers = async () => { setLoading(true); try { setUsers((await api.adminGetUsers()).users); } catch (e) { console.error(e); } finally { setLoading(false); } };
  const loadPrompts = async () => { setLoading(true); try { setPrompts((await api.adminGetPrompts()).prompts); } catch (e) { console.error(e); } finally { setLoading(false); } };
  const loadTopics = async () => { setLoading(true); try { setTopics((await api.adminGetTopics()).topics); } catch (e) { console.error(e); } finally { setLoading(false); } };
  const loadScheduler = async () => { setLoading(true); try { setSchedulerData(await api.adminGetScheduler()); } catch (e) { console.error(e); } finally { setLoading(false); } };
  const loadPublished = async () => { setLoading(true); try { setPublishedCards((await api.adminGetPublished()).published); } catch (e) { console.error(e); } finally { setLoading(false); } };

  const showMsg = (msg) => { setMessage(msg); setTimeout(() => setMessage(''), 3000); };

  const handleUpdateUserStatus = async (userId, status) => {
    try {
      await api.adminUpdateUserStatus(userId, status);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, status } : u));
      showMsg(`User ${status}`);
    } catch (e) { console.error(e); }
  };

  const handleSavePrompt = async (prompt) => {
    setSaving(true);
    try {
      await api.adminUpdatePrompt(prompt.id, {
        prompt_key: prompt.prompt_key,
        system_prompt: editSystemPrompt,
        task_prompt: editTaskPrompt,
      });
      setPrompts(prev => prev.map(p => p.id === prompt.id
        ? { ...p, system_prompt: editSystemPrompt, task_prompt: editTaskPrompt } : p));
      setEditingPrompt(null);
      showMsg('Prompt updated');
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  const handleAddTopic = async () => {
    if (!newTopic.title.trim()) return;
    setSaving(true);
    try {
      const res = await api.adminCreateTopic(newTopic);
      setTopics(prev => [res.topic, ...prev]);
      setNewTopic({ title: '', category: 'technology', trend_score: 50 });
      setShowAddTopic(false);
      showMsg('Topic added');
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  const handleDeleteTopic = async (topicId) => {
    try {
      await api.adminDeleteTopic(topicId);
      setTopics(prev => prev.filter(t => t.id !== topicId));
      showMsg('Topic deleted');
    } catch (e) { console.error(e); }
  };

  const handleManualRefresh = async () => {
    setRefreshing(true);
    try {
      await api.refreshTrending();
      showMsg('Data refresh triggered');
      setTimeout(loadScheduler, 2000);
    } catch (e) { console.error(e); }
    finally { setRefreshing(false); }
  };

  const handlePublishNow = async () => {
    setRefreshing(true);
    try {
      await api.adminPublishNow();
      showMsg('Auto-publish triggered');
      setTimeout(loadPublished, 3000);
    } catch (e) { console.error(e); }
    finally { setRefreshing(false); }
  };

  const filteredUsers = users.filter(u =>
    !userSearch || (u.name + u.email + u.mobile).toLowerCase().includes(userSearch.toLowerCase())
  );

  return (
    <div data-testid="admin-panel" className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="bg-white border-b border-gray-100 px-5 py-3 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-2">
          <img src="https://customer-assets.emergentagent.com/job_web-pulse-4/artifacts/i5z1wfjq_WTFH%20logo.png" alt="WTFHappened" className="h-7 object-contain" />
          <span className="text-sm font-bold text-gray-900">Admin</span>
        </div>
        <button data-testid="admin-logout" onClick={onLogout}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-500 hover:bg-gray-100 transition-colors">
          <LogOut size={14} /> Logout
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1.5 px-5 py-3 overflow-x-auto">
        {ADMIN_TABS.map(t => (
          <button key={t.key} data-testid={`admin-tab-${t.key}`} onClick={() => setTab(t.key)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all
              ${tab === t.key ? 'bg-gray-900 text-white' : 'bg-white text-gray-500 hover:bg-gray-100 border border-gray-200'}`}>
            <t.icon size={14} />{t.label}
          </button>
        ))}
      </div>

      {/* Feedback */}
      <AnimatePresence>
        {message && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="mx-5 mb-3 px-4 py-2 rounded-xl bg-green-50 text-green-700 text-xs font-medium text-center">{message}</motion.div>
        )}
      </AnimatePresence>

      <div className="px-5 pb-10">
        {/* OVERVIEW */}
        {tab === 'overview' && stats && (
          <div className="grid grid-cols-2 gap-3 mt-2">
            {[
              { label: 'Total Users', value: stats.total_users, color: 'bg-blue-50 text-blue-700' },
              { label: 'Active Users', value: stats.active_users, color: 'bg-green-50 text-green-700' },
              { label: 'Trial Users', value: stats.trial_users, color: 'bg-yellow-50 text-yellow-700' },
              { label: 'Paid Users', value: stats.paid_users, color: 'bg-purple-50 text-purple-700' },
              { label: 'Topics', value: stats.total_topics, color: 'bg-orange-50 text-orange-700' },
              { label: 'Explanations', value: stats.total_explanations, color: 'bg-teal-50 text-teal-700' },
            ].map(s => (
              <div key={s.label} className={`${s.color} rounded-2xl p-4`}>
                <p className="text-[10px] font-bold tracking-widest uppercase opacity-60">{s.label}</p>
                <p className="text-2xl font-extrabold mt-1">{s.value}</p>
              </div>
            ))}
          </div>
        )}

        {/* USERS */}
        {tab === 'users' && (
          <div className="mt-2">
            <div className="relative mb-3">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input data-testid="admin-user-search" value={userSearch} onChange={e => setUserSearch(e.target.value)}
                placeholder="Search users..." className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-white border border-gray-200 text-sm outline-none focus:border-gray-400" />
            </div>
            {loading ? <div className="text-center py-10"><Loader2 size={24} className="animate-spin mx-auto text-gray-400" /></div> : (
              <div className="space-y-2">
                {filteredUsers.map(u => (
                  <div key={u.id} className="bg-white rounded-xl border border-gray-100 p-3">
                    <div className="flex items-center justify-between">
                      <div className="min-w-0 flex-1 mr-2">
                        <p className="text-sm font-semibold text-gray-900 truncate">{u.name}</p>
                        <p className="text-xs text-gray-400 truncate">{u.email || u.mobile}</p>
                        <div className="flex gap-2 mt-1">
                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase
                            ${u.subscription_status === 'active' ? 'bg-green-50 text-green-600'
                              : u.subscription_status === 'trial' ? 'bg-blue-50 text-blue-600'
                              : 'bg-gray-100 text-gray-500'}`}>
                            {u.subscription_status || 'unknown'}
                          </span>
                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase
                            ${u.status === 'active' ? 'bg-green-50 text-green-600'
                              : u.status === 'suspended' ? 'bg-yellow-50 text-yellow-600'
                              : 'bg-red-50 text-red-600'}`}>
                            {u.status || 'active'}
                          </span>
                        </div>
                      </div>
                      <select data-testid={`admin-user-status-${u.id}`}
                        value={u.status || 'active'}
                        onChange={e => handleUpdateUserStatus(u.id, e.target.value)}
                        className="text-xs bg-gray-50 border border-gray-200 rounded-lg px-2 py-1.5 outline-none">
                        <option value="active">Active</option>
                        <option value="suspended">Suspended</option>
                        <option value="banned">Banned</option>
                      </select>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* PROMPTS */}
        {tab === 'prompts' && (
          <div className="mt-2 space-y-3">
            <p className="text-xs text-gray-400 mb-1">3-step AI pipeline: Fact Extraction → Driver Analysis → Card Generation</p>
            {loading ? <div className="text-center py-10"><Loader2 size={24} className="animate-spin mx-auto text-gray-400" /></div> : (
              prompts.map((p, idx) => (
                <div key={p.id} className="bg-white rounded-xl border border-gray-100 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <p className="text-sm font-bold text-gray-900">{p.label || p.prompt_key}</p>
                      {p.description && <p className="text-[10px] text-gray-400 mt-0.5">{p.description}</p>}
                    </div>
                    {editingPrompt === p.id ? (
                      <div className="flex gap-1">
                        <button onClick={() => setEditingPrompt(null)} className="p-1 rounded-lg hover:bg-gray-100"><X size={14} /></button>
                        <button data-testid={`save-prompt-${idx}`} onClick={() => handleSavePrompt(p)} disabled={saving}
                          className="p-1 rounded-lg hover:bg-green-100 text-green-600">
                          {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                        </button>
                      </div>
                    ) : (
                      <button data-testid={`edit-prompt-${idx}`}
                        onClick={() => { setEditingPrompt(p.id); setEditSystemPrompt(p.system_prompt || ''); setEditTaskPrompt(p.task_prompt || ''); }}
                        className="p-1 rounded-lg hover:bg-gray-100"><Edit3 size={14} className="text-gray-400" /></button>
                    )}
                  </div>
                  {editingPrompt === p.id ? (
                    <div className="space-y-3">
                      <div>
                        <label className="text-[10px] font-bold text-gray-500 tracking-widest uppercase block mb-1">System Prompt</label>
                        <textarea data-testid={`system-prompt-${idx}`} value={editSystemPrompt} onChange={e => setEditSystemPrompt(e.target.value)}
                          rows={5} className="w-full text-xs bg-gray-50 border border-gray-200 rounded-lg p-3 outline-none focus:border-gray-400 font-mono resize-y" />
                      </div>
                      <div>
                        <label className="text-[10px] font-bold text-gray-500 tracking-widest uppercase block mb-1">Task Prompt</label>
                        <textarea data-testid={`task-prompt-${idx}`} value={editTaskPrompt} onChange={e => setEditTaskPrompt(e.target.value)}
                          rows={8} className="w-full text-xs bg-gray-50 border border-gray-200 rounded-lg p-3 outline-none focus:border-gray-400 font-mono resize-y" />
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div>
                        <p className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-0.5">System Prompt</p>
                        <p className="text-xs text-gray-500 font-mono whitespace-pre-wrap line-clamp-3">{p.system_prompt}</p>
                      </div>
                      <div>
                        <p className="text-[9px] font-bold text-gray-400 tracking-widest uppercase mb-0.5">Task Prompt</p>
                        <p className="text-xs text-gray-500 font-mono whitespace-pre-wrap line-clamp-3">{p.task_prompt}</p>
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* TOPICS */}
        {tab === 'topics' && (
          <div className="mt-2">
            <button data-testid="admin-add-topic" onClick={() => setShowAddTopic(!showAddTopic)}
              className="w-full mb-3 py-2.5 rounded-xl bg-gray-900 text-white text-sm font-semibold flex items-center justify-center gap-2 hover:bg-gray-800 transition-all">
              <Plus size={16} /> Add Topic
            </button>

            <AnimatePresence>
              {showAddTopic && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                  className="bg-white rounded-xl border border-gray-100 p-4 mb-3 space-y-2">
                  <input data-testid="new-topic-title" value={newTopic.title} onChange={e => setNewTopic({ ...newTopic, title: e.target.value })}
                    placeholder="Topic title" className="w-full px-3 py-2 rounded-lg bg-gray-50 border border-gray-200 text-sm outline-none" />
                  <div className="flex gap-2">
                    <select data-testid="new-topic-category" value={newTopic.category} onChange={e => setNewTopic({ ...newTopic, category: e.target.value })}
                      className="flex-1 px-3 py-2 rounded-lg bg-gray-50 border border-gray-200 text-sm outline-none">
                      {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                    <input data-testid="new-topic-score" type="number" min="0" max="100" value={newTopic.trend_score}
                      onChange={e => setNewTopic({ ...newTopic, trend_score: Number(e.target.value) })}
                      className="w-20 px-3 py-2 rounded-lg bg-gray-50 border border-gray-200 text-sm outline-none" />
                  </div>
                  <button data-testid="save-new-topic" onClick={handleAddTopic} disabled={saving || !newTopic.title.trim()}
                    className="w-full py-2.5 rounded-lg bg-green-600 text-white text-sm font-semibold hover:bg-green-700 disabled:opacity-60 transition-all">
                    {saving ? <Loader2 size={14} className="animate-spin mx-auto" /> : 'Save Topic'}
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            {loading ? <div className="text-center py-10"><Loader2 size={24} className="animate-spin mx-auto text-gray-400" /></div> : (
              <div className="space-y-2">
                {topics.map(t => (
                  <div key={t.id} className="bg-white rounded-xl border border-gray-100 p-3 flex items-center justify-between">
                    <div className="min-w-0 flex-1 mr-2">
                      <p className="text-sm font-medium text-gray-900 truncate">{t.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 uppercase">{t.category}</span>
                        <span className="text-[9px] text-gray-400">Score: {t.trend_score}</span>
                        <span className="text-[9px] text-gray-400">{t.source}</span>
                      </div>
                    </div>
                    <button data-testid={`delete-topic-${t.id}`} onClick={() => handleDeleteTopic(t.id)}
                      className="p-2 rounded-lg hover:bg-red-50 text-red-400 hover:text-red-600 transition-colors">
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* SCHEDULER */}
        {tab === 'scheduler' && (
          <div className="mt-2 space-y-3">
            {loading ? <div className="text-center py-10"><Loader2 size={24} className="animate-spin mx-auto text-gray-400" /></div> : schedulerData && (
              <>
                <div className="bg-white rounded-2xl border border-gray-100 p-4">
                  <p className="text-xs font-bold text-gray-500 tracking-widest uppercase mb-3">Data Refresh</p>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Status</span>
                      <span className={`text-xs font-bold px-2 py-1 rounded-lg ${schedulerData.data_refresh?.running ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}`}>
                        {schedulerData.data_refresh?.running ? 'Active' : 'Stopped'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Interval</span>
                      <span className="text-sm font-semibold text-gray-900">{schedulerData.data_refresh?.interval_minutes} min</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Next Run</span>
                      <span className="text-xs text-gray-500">{schedulerData.data_refresh?.next_run ? new Date(schedulerData.data_refresh.next_run).toLocaleTimeString() : 'N/A'}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Last Run</span>
                      <span className="text-xs text-gray-500">{schedulerData.data_refresh?.last_run ? new Date(schedulerData.data_refresh.last_run).toLocaleString() : 'Never'}</span>
                    </div>
                  </div>
                  <button data-testid="manual-refresh-btn" onClick={handleManualRefresh} disabled={refreshing}
                    className="w-full mt-3 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold flex items-center justify-center gap-2 hover:bg-blue-700 disabled:opacity-60 transition-all">
                    {refreshing ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />} Refresh Now
                  </button>
                </div>

                <div className="bg-white rounded-2xl border border-gray-100 p-4">
                  <p className="text-xs font-bold text-gray-500 tracking-widest uppercase mb-3">Auto Publisher</p>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Status</span>
                      <span className={`text-xs font-bold px-2 py-1 rounded-lg ${schedulerData.auto_publisher?.running ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}`}>
                        {schedulerData.auto_publisher?.running ? 'Active' : 'Stopped'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Next Run</span>
                      <span className="text-xs text-gray-500">{schedulerData.auto_publisher?.next_run ? new Date(schedulerData.auto_publisher.next_run).toLocaleTimeString() : 'N/A'}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Last Run</span>
                      <span className="text-xs text-gray-500">{schedulerData.auto_publisher?.last_run ? new Date(schedulerData.auto_publisher.last_run).toLocaleString() : 'Never'}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-amber-50 rounded-2xl p-4">
                  <p className="text-xs font-semibold text-amber-800 mb-1">Data Sources Active</p>
                  <p className="text-[11px] text-amber-700 leading-relaxed">
                    CoinGecko, Hacker News, Google Trends, X/Twitter, BBC, TMZ, Vogue, E! News, Wikipedia
                  </p>
                  <p className="text-[11px] text-amber-600 mt-1">Reddit: Requires OAuth2 credentials</p>
                </div>
              </>
            )}
          </div>
        )}

        {/* PUBLISHER */}
        {tab === 'publisher' && (
          <div className="mt-2 space-y-3">
            <button data-testid="publish-now-btn" onClick={handlePublishNow} disabled={refreshing}
              className="w-full py-2.5 rounded-xl bg-gray-900 text-white text-sm font-semibold flex items-center justify-center gap-2 hover:bg-gray-800 disabled:opacity-60 transition-all">
              {refreshing ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />} Publish Top Cards Now
            </button>
            {loading ? <div className="text-center py-10"><Loader2 size={24} className="animate-spin mx-auto text-gray-400" /></div> : (
              publishedCards.length === 0 ? (
                <div className="text-center py-10">
                  <p className="text-sm text-gray-400">No cards published yet</p>
                  <p className="text-xs text-gray-300 mt-1">Cards with score 70+ will be auto-published every 30 min</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {publishedCards.map(card => (
                    <div key={card.id} className="bg-white rounded-xl border border-gray-100 p-3">
                      <p className="text-sm font-medium text-gray-900 truncate">{card.topic_title}</p>
                      <div className="flex items-center gap-2 mt-1.5">
                        {Object.entries(card.platforms || {}).map(([platform, result]) => (
                          <span key={platform} className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase
                            ${result.status === 'published' ? 'bg-green-50 text-green-600'
                              : result.status === 'skipped' ? 'bg-yellow-50 text-yellow-600'
                              : 'bg-red-50 text-red-600'}`}>
                            {platform}: {result.status}
                          </span>
                        ))}
                      </div>
                      <p className="text-[10px] text-gray-400 mt-1">{new Date(card.published_at).toLocaleString()}</p>
                    </div>
                  ))}
                </div>
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
}
