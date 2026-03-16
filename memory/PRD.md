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
- Security headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, HSTS, Cache-Control: no-store for API
- Rate limiting: 10/min on auth endpoints, 5/min per user on AI endpoints, 60/min default
- Request logging with X-Request-ID for traceability
- Global exception handler with standardized error responses
- CORS configured with specific origins (not wildcard)
- JWT with persisted cryptographic secret (fail-fast if missing)
- JWT refresh token flow with rotation (old tokens invalidated on use)
- Security audit logging: every auth event logged to DB (login, register, password reset, failures)
- API usage tracking: monitors AI/expensive endpoint calls with hourly/daily stats
- Admin endpoints: /admin/audit-log, /admin/api-usage for security monitoring
- No hardcoded secrets — ADMIN_PASSWORD, JWT_SECRET required in .env (fail-fast)
- MongoDB connection pooling (maxPoolSize=20, minPoolSize=2)
- .env.example documenting all required variables
- README.md with full API documentation

## User Personas
- **Consumer**: Ages 15-35, wants quick understanding of trending topics
- **Content Creator**: Wants shareable explanation cards
- **Admin**: Manages app content, users, AI prompts, scheduler

## What's Been Implemented

### Phase 1 - Core App
- Trending feed with seed topics, category filtering, trend scores
- AI explanation engine (Claude Sonnet) with 3-card system: What / Why / Why It Matters To You
- Explain This input with AI-powered explanations
- Save/bookmark system (user-specific)
- Social card generator with 3 templates (Square, Twitter, Story)
- Data collection services (CoinGecko, Wikipedia, Hacker News, Google Trends, X/Twitter)

### Phase 1.5 - Auth & Onboarding
- Email/mobile registration and login (JWT + bcrypt)
- 7-step onboarding: Welcome, Interests (25 items), Curiosity Type (14 items), Depth, Location, Professional Context, Follow Topics
- Profile menu with logout
- Sign Out button on onboarding welcome screen

### Phase 2 - Advanced Features
- Forgot/Reset Password: Token-based flow
- Terms & Conditions page
- Stripe Subscription: $4.99/month with 2-day free trial
- Settings Page: 4 tabs (Subscription, Profile, Preferences, Account)
- Admin Panel: 6 tabs (Overview, Users, AI Prompts, News Feed, Scheduler, Publisher)

### Phase 3 - Data Sources & Automation (2026-03-15)
- RSS feed integration: TMZ, Vogue, E! News, BBC News, BBC Tech, BBC Science
- Parallel data collection using asyncio.gather
- Background scheduler: Auto-refresh data every 10 minutes
- Auto-publisher infrastructure: Selects top cards (score >= 70) and publishes to X/Twitter every 30 minutes
- New categories: entertainment, lifestyle
- Category filters updated: Celeb, Style tabs added
- Custom logo integration across all screens

## Admin Credentials
- Email: admin@wtfhappened.app
- Password: WTFadmin2026!

## Prioritized Backlog
### P0 (Done)
- [x] Core trending feed + AI explanations
- [x] Auth + Onboarding (25 interests, 14 curiosity types)
- [x] Settings + Subscription
- [x] Admin Panel (6 tabs)
- [x] Forgot/Reset Password
- [x] Terms & Conditions
- [x] RSS feed data sources (lifestyle/news)
- [x] Background scheduler (10-min auto-refresh)
- [x] Auto-publisher infrastructure
- [x] Custom logo integration
- [x] Onboarding Sign Out button fix

### P1 (Important)
- [x] PWA capabilities (service worker, manifest, offline caching, install prompt)
- [x] Personalized feed based on user interests from onboarding ("Your News" tab, default for logged-in users)
- [x] Email service for password reset delivery (Resend API — test mode, needs verified domain for production)
- [ ] Stripe webhook production setup
- [ ] X/Twitter auto-publish: needs OAuth 1.0a write tokens (X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET)

### P2 (Nice to Have)
- [ ] Reddit integration (requires OAuth2 credentials from user)
- [ ] Push notifications for trending topics
- [ ] Server-side image rendering for social cards
- [ ] Redis caching layer
- [ ] NewsAPI, YouTube Trending, TMDb integration (requires API keys)
- [ ] Social media publishing for Instagram/Facebook
- [ ] Card-to-video generator for TikTok

## Next Tasks
1. PWA manifest + service worker
2. Personalize feed based on user onboarding preferences
3. Email service for password reset delivery
4. Get X/Twitter OAuth 1.0a write tokens from user for auto-publishing
