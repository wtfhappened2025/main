# WTFHappened - Product Requirements Document

## Original Problem Statement
Build a consumer web app/PWA that explains trending topics using AI-generated 3-card explanations (What Happened, Why It Happened, Why It Matters To You). Personalized explanations addressing the reader directly.

## Architecture
- **Frontend**: React 19 + TailwindCSS + Framer Motion (mobile-first PWA)
- **Backend**: FastAPI (Python) — modular structure following best practices
  - `server.py` (78 lines) — app init, middleware, lifecycle
  - `config.py` — Settings class, centralized env management
  - `database.py` — MongoDB connection with retry, health check, indexes
  - `middleware/` — Security headers, request logging, rate limiting
  - `models/` — Pydantic request/response models
  - `routes/` — auth.py, content.py, subscription.py, admin.py, system.py
  - `services/` — ai_engine.py, data_collector.py, publisher.py, scheduler.py
  - `utils/` — security.py (JWT, auth), helpers.py (shared constants/functions)
- **Database**: MongoDB
- **AI Engine**: Claude Sonnet via Emergent Universal Key
- **Payments**: Stripe via emergentintegrations library
- **Data Sources**: CoinGecko, Wikipedia, Hacker News, Google Trends, X/Twitter, RSS Feeds (BBC, TMZ, Vogue, E! News)

### Security & Best Practices (implemented 2026-03-15/16)
- Security headers, rate limiting, request logging, JWT with refresh tokens
- Security audit logging, API usage tracking
- No hardcoded secrets — fail-fast config

## User Personas
- **Consumer**: Ages 15-35, wants quick understanding of trending topics
- **Content Creator**: Wants shareable explanation cards
- **Admin**: Manages app content, users, AI prompts, scheduler

## App Flow
1. **Splash Screen** (`SplashScreen.js`) → animated gradient + floating emojis + CTA
2. **Auth** (`AuthScreen.js`) → sign up / sign in
3. **Onboarding** (`OnboardingFlow.js`) → 7-step user preferences
4. **Home Dashboard** (`HomePage.js`) → stats + top 3 topics + "Browse All Topics"
5. **News Feed** (`TrendingFeed.js`) → full mosaic feed with cards (swipe, bookmark, reactions)
6. **Explanation View** (`ExplanationView.js`) → 3 cards: WHAT / WHY / YOU (split into affects + action)

## What's Been Implemented

### Phase 1 - Core App
- Trending feed with seed topics, category filtering, trend scores
- AI explanation engine (Claude Sonnet) with 3-card system
- Explain This input with AI-powered explanations
- Save/bookmark system (user-specific)
- Social card generator with 3 templates

### Phase 1.5 - Auth & Onboarding
- Email/mobile registration and login (JWT + bcrypt)
- 7-step onboarding
- Profile menu with logout

### Phase 2 - Advanced Features
- Forgot/Reset Password with Resend email delivery
- Terms & Conditions page
- Stripe Subscription: $4.99/month
- Settings Page: 4 tabs
- Admin Panel: 6 tabs

### Phase 3 - Data Sources & Automation
- RSS feed integration (TMZ, Vogue, E! News, BBC)
- Parallel data collection, background scheduler
- Auto-publisher infrastructure

### Phase 4 - Security Hardening (2026-03-15/16)
- Modular backend refactor
- JWT refresh tokens, audit logging, API usage tracking
- Per-user rate limiting, security headers

### Phase 5 - UX Redesign (2026-03-16)
- Dashboard mosaic feed with 3D-tilt cards, sparklines
- Swipe-to-dismiss on cards
- Bookmark/save button on each card
- Emoji reactions (fire, shocked, mindblown, angry) with toggle + counts
- "Read in 3 cards" CTA on cards
- Split "You" card into "How it affects you" + "What you should do"
- Splash screen (animated gradient, floating emojis, CTA)
- Home dashboard page (stats, top 3 topics, Browse All Topics)
- Renamed TRENDING tab to HOME in bottom nav
- PWA capabilities (manifest, service worker, install prompt)
- Personalized "Your News" feed

## Admin Credentials
- Email: admin@wtfhappened.app
- Password: WTFadmin2026!

## Prioritized Backlog

### P0 (Done)
- [x] All core features implemented
- [x] Full page flow: Splash → Auth → Onboarding → Home → Feed
- [x] Card interactions: swipe, bookmark, emoji reactions
- [x] Split "You" card into affects + action sections
- [x] Security hardening + modular backend

### P1 (Next)
- [ ] Auto social media publishing (X/Twitter) — scheduler job exists, calls placeholder
- [ ] Push notifications for trending topics
- [ ] Comprehensive test suite (>60% coverage)

### P2 (Nice to Have)
- [ ] Reddit integration (requires OAuth2 credentials)
- [ ] Server-side image rendering for social cards
- [ ] Redis caching layer
- [ ] Extract TopicCard from TrendingFeed.js into own component

### P3 (Backlog — Production Setup)
- [ ] Stripe webhook production setup
- [ ] X/Twitter OAuth 1.0a write tokens
- [ ] Verify Resend domain for production email
- [ ] Cloud secret manager integration
- [ ] IP allowlisting for external API keys

## Key API Endpoints
- `/api/auth/register`, `/api/auth/login`, `/api/auth/forgot-password`
- `/api/token/refresh`
- `/api/feed`, `/api/feed/personalized`
- `/api/explanation/{topic_id}`, `/api/explain`
- `/api/react/{topic_id}`, `/api/reactions/mine`
- `/api/save/{topic_id}`, `/api/saved`
- `/api/dismiss/{topic_id}`
- `/api/admin/*`
