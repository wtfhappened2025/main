# WTFHappened - Product Requirements Document

## Original Problem Statement
Build a consumer web app/PWA that explains trending topics using AI-generated 3-card explanations (What Happened, Why It Happened, Why It Matters To You). Based on 11 specification documents. Personalized explanations addressing the reader directly.

## Architecture
- **Frontend**: React 19 + TailwindCSS + Framer Motion (mobile-first)
- **Backend**: FastAPI (Python) with modular services
- **Database**: MongoDB (collections: topics, explanations, saved_topics, users, payment_transactions, password_resets, ai_prompts)
- **AI Engine**: Claude Sonnet via Emergent Universal Key
- **Payments**: Stripe via emergentintegrations library
- **Data Sources**: CoinGecko, Wikipedia, Reddit (free public APIs)

## User Personas
- **Consumer**: Ages 15-35, wants quick understanding of trending topics
- **Content Creator**: Wants shareable explanation cards
- **Admin**: Manages app content, users, AI prompts

## What's Been Implemented

### Phase 1 - Core App (2026-03-15)
- Trending feed with 8 seed topics, category filtering, trend scores
- AI explanation engine (Claude Sonnet) with 3-card system: What / Why / Why It Matters To You
- Explain This input with AI-powered explanations
- Save/bookmark system (user-specific)
- Social card generator with 3 templates (Square, Twitter, Story)
- Data collection services (CoinGecko, Wikipedia, Reddit)

### Phase 1.5 - Auth & Onboarding (2026-03-15)
- Email/mobile registration and login (JWT + bcrypt)
- 7-step onboarding: Welcome, Interests, Curiosity Type, Depth, Location, Professional Context, Follow Topics
- Profile menu with logout

### Phase 2 - Advanced Features (2026-03-15)
- **Forgot/Reset Password**: Token-based flow with email/mobile recovery
- **Terms & Conditions**: Legal page with acceptance text on registration
- **Stripe Subscription**: $4.99/month with 2-day free trial, auto-renew toggle, checkout session via Stripe
- **Settings Page**: 4 tabs - Subscription (plan status, subscribe, auto-renew), Profile (edit name/email/mobile, change password), Preferences (interests, depth), Account (sign out, suspend, delete with confirmation)
- **Admin Panel**: Separate admin login with 4 sections - Overview (stats dashboard), Users (search, view status, change status), AI Prompts (view/edit system/explanation/caption prompts), News Feed (add/delete topics)

### Testing Results
- Iteration 1: 100% backend, 95% frontend
- Iteration 2: 95.2% backend (20/21), 85% frontend (17/20) — no critical bugs

## Admin Credentials
- Email: admin@wtfhappened.app
- Password: WTFadmin2026!

## Prioritized Backlog
### P0 (Done)
- [x] Core trending feed + AI explanations
- [x] Auth + Onboarding
- [x] Settings + Subscription
- [x] Admin Panel
- [x] Forgot/Reset Password
- [x] Terms & Conditions

### P1 (Important)
- [ ] PWA capabilities (service worker, manifest, offline caching, install prompt)
- [ ] Real-time data ingestion scheduler (every 10 min)
- [ ] Email service for password reset delivery (SendGrid/Resend)
- [ ] Personalized feed based on user interests from onboarding
- [ ] Stripe webhook production setup

### P2 (Nice to Have)
- [ ] Automatic Social Media Publisher (X, LinkedIn, Instagram APIs)
- [ ] Push notifications for trending topics
- [ ] Server-side image rendering for social cards
- [ ] Redis caching layer
- [ ] NewsAPI integration (requires API key)

## Next Tasks
1. Add PWA manifest + service worker
2. Set up scheduled data collection (every 10 min)
3. Integrate email service for password reset delivery
4. Personalize feed based on user onboarding preferences
5. Build auto-publisher system (Phase 2 from original spec)
