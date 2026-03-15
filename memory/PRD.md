# WTFHappened - Product Requirements Document

## Original Problem Statement
Build a consumer web app/PWA that explains trending topics on the internet using AI-generated 3-card explanations (What Happened, Why It Happened, Why It Matters). Based on 11 specification documents covering functional spec, technical spec, AI engine, data sourcing, social card templates, auto-publisher, backend architecture, and best practices.

## Architecture
- **Frontend**: React 19 + TailwindCSS + Framer Motion (mobile-first PWA-ready)
- **Backend**: FastAPI (Python) with modular services
- **Database**: MongoDB (collections: topics, explanations, saved_topics)
- **AI Engine**: Claude Sonnet via Emergent Universal Key (emergentintegrations library)
- **Data Sources**: CoinGecko, Wikipedia, Reddit (free public APIs)

## User Personas
- **Primary**: Ages 15-35, want quick understanding of trending news/tech/finance/culture
- **Secondary**: Content creators wanting shareable explanation cards

## Core Requirements (Static)
1. Trending Feed - topics sorted by trend score with category filtering
2. AI Explanation Engine - 3-card explanations (What/Why/Matters)
3. Explain This Tool - user pastes headline, gets AI explanation
4. Trending Confusion Index - topics people are searching/asking about
5. Social Card Generator - shareable visual cards in multiple formats
6. Save/Bookmark system
7. Automatic Social Media Publisher (Phase 2)

## What's Been Implemented (2026-03-15)
- **Phase 1 Complete**: Core app with all 6 main features
  - Trending feed with 8 seed topics, category filtering, trend scores
  - AI explanation engine (Claude Sonnet via Emergent key)
  - Explain This input with suggestions
  - Save/bookmark system
  - Social card generator with 3 templates (Square, Twitter, Story)
  - Caption generation for social sharing
  - Data collection services (CoinGecko, Wikipedia, Reddit)
  - Full API: /feed, /explanation, /explain, /trending, /save, /saved, /render-card, /refresh-trending, /health
- **Testing**: 100% backend (13/13), 95% frontend (25/26)

## Prioritized Backlog
### P0 (Critical)
- [x] Core trending feed
- [x] AI explanation engine
- [x] Explain This tool
- [x] Save/bookmark

### P1 (Important)
- [ ] PWA capabilities (service worker, manifest, offline caching, install prompt)
- [ ] Real-time data ingestion scheduler (5-10 min intervals)
- [ ] Topic deduplication and clustering
- [ ] Trend scoring algorithm improvements

### P2 (Nice to Have)
- [ ] Automatic Social Media Publisher (X, LinkedIn, Instagram APIs)
- [ ] User authentication and profiles
- [ ] Personalization (interest selection, feed prioritization)
- [ ] Push notifications for trending topics
- [ ] Image rendering service for social cards (server-side)
- [ ] Redis caching layer
- [ ] NewsAPI integration (requires API key)
- [ ] Visual generation (charts, timelines) for explanation cards

## Next Tasks
1. Add PWA manifest + service worker for installability
2. Set up scheduled data collection jobs (every 10 min)
3. Implement topic deduplication across sources
4. Add user auth (JWT or Google OAuth)
5. Build auto-publisher system with mock posting
