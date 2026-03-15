# WTFHappened

> Trending topics explained in 3 cards. No noise, just clarity.

## Architecture

```
/app/backend/
├── server.py            # FastAPI app init, middleware, lifecycle (~80 lines)
├── config.py            # Settings class, env management
├── database.py          # MongoDB connection, indexes, health check
├── models/              # Pydantic request/response models
│   └── __init__.py
├── routes/              # API route handlers (one file per domain)
│   ├── auth.py          # Registration, login, onboarding, password reset
│   ├── content.py       # Feed, explanations, save/bookmark, social cards
│   ├── subscription.py  # Stripe checkout, status, webhook
│   ├── admin.py         # Admin CRUD (users, prompts, topics, publisher)
│   └── system.py        # Health check, scheduler status, refresh
├── services/            # Business logic
│   ├── ai_engine.py     # 3-step Claude AI pipeline
│   ├── data_collector.py# RSS feeds, CoinGecko, HackerNews, Google Trends, X/Twitter
│   ├── publisher.py     # Auto social media publishing
│   └── scheduler.py     # Background jobs (data refresh, auto-publish)
├── middleware/           # CORS, security headers, rate limiting, logging
│   └── __init__.py
├── utils/               # Shared utilities
│   ├── security.py      # JWT, password hashing, auth dependencies
│   └── helpers.py       # time_ago, safe_user, category constants
└── tests/               # Automated tests
```

## Quick Start

```bash
cp .env.example .env     # Fill in your values
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```

## API Endpoints

### Auth
- `POST /api/auth/register` — Create account
- `POST /api/auth/login` — Login
- `GET  /api/auth/me` — Get current user
- `PUT  /api/auth/onboarding` — Save onboarding preferences
- `POST /api/auth/forgot-password` — Request password reset
- `POST /api/auth/reset-password` — Reset password with token

### Content
- `GET  /api/feed` — Trending topics feed
- `GET  /api/feed/personalized` — Personalized feed (auth required)
- `GET  /api/explanation/{topic_id}` — Get/generate explanation
- `POST /api/explain` — Explain user-submitted topic
- `POST /api/save/{topic_id}` — Save/unsave topic
- `GET  /api/saved` — Get saved topics

### Subscription
- `GET  /api/subscription/info` — Subscription status
- `POST /api/subscription/checkout` — Create Stripe checkout
- `GET  /api/subscription/status/{session_id}` — Check payment

### Admin (requires admin auth)
- `POST /api/admin/login` — Admin login
- `GET  /api/admin/users` — List users
- `GET  /api/admin/prompts` — Get AI prompts
- `GET  /api/admin/topics` — List topics
- `GET  /api/admin/scheduler` — Scheduler status
- `GET  /api/admin/published` — Published cards

### System
- `GET  /api/health` — Health check
- `GET  /api/scheduler/status` — Scheduler info
- `POST /api/refresh-trending` — Manual data refresh

## Data Sources
CoinGecko, Wikipedia, Hacker News, Google Trends, X/Twitter, BBC, TMZ, Vogue, E! News

## Tech Stack
FastAPI, MongoDB, Claude AI (Emergent), Stripe, APScheduler
