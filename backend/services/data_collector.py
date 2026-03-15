import httpx
import logging
import random
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Category mapping for different sources
CATEGORY_MAP = {
    "technology": "technology",
    "business": "finance",
    "science": "science",
    "health": "science",
    "entertainment": "internet_culture",
    "sports": "world_news",
    "general": "world_news",
}


async def fetch_coingecko_trending() -> list:
    """Fetch trending coins from CoinGecko (free, no key)."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://api.coingecko.com/api/v3/search/trending")
            if resp.status_code == 200:
                data = resp.json()
                topics = []
                for coin in data.get("coins", [])[:5]:
                    item = coin.get("item", {})
                    name = item.get("name", "")
                    symbol = item.get("symbol", "")
                    score = item.get("score", 0)
                    price_change = item.get("data", {}).get("price_change_percentage_24h", {}).get("usd", 0)
                    direction = "surging" if price_change and price_change > 0 else "dropping"
                    topics.append({
                        "title": f"Why {name} ({symbol}) is {direction} today",
                        "category": "crypto",
                        "source": "coingecko",
                        "trend_score": max(60, 95 - score * 5),
                        "raw_data": {"name": name, "symbol": symbol, "price_change_24h": price_change}
                    })
                return topics
    except Exception as e:
        logger.error(f"CoinGecko fetch failed: {e}")
    return []


async def fetch_wikipedia_trending() -> list:
    """Fetch most viewed Wikipedia articles (proxy for trending topics)."""
    try:
        today = datetime.now(timezone.utc)
        date_str = today.strftime("%Y/%m/%d")
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{date_str}"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                articles = data.get("items", [{}])[0].get("articles", [])
                topics = []
                # Filter out generic pages
                skip = {"Main_Page", "Special:Search", "-", "Wikipedia:Main_Page"}
                for article in articles[:30]:
                    title = article.get("article", "")
                    if title in skip or title.startswith("Special:") or title.startswith("Wikipedia:"):
                        continue
                    clean_title = title.replace("_", " ")
                    views = article.get("views", 0)
                    topics.append({
                        "title": f"Why is {clean_title} trending right now",
                        "category": "world_news",
                        "source": "wikipedia",
                        "trend_score": min(95, max(50, int(views / 10000))),
                        "raw_data": {"article": clean_title, "views": views}
                    })
                    if len(topics) >= 5:
                        break
                return topics
    except Exception as e:
        logger.error(f"Wikipedia fetch failed: {e}")
    return []


async def fetch_reddit_trending() -> list:
    """Fetch trending posts from Reddit public JSON."""
    try:
        headers = {"User-Agent": "WTFHappened/1.0"}
        subreddits = ["worldnews", "technology", "science", "OutOfTheLoop"]
        topics = []
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            for sub in subreddits:
                try:
                    resp = await client.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=3")
                    if resp.status_code == 200:
                        data = resp.json()
                        posts = data.get("data", {}).get("children", [])
                        for post in posts[:2]:
                            pdata = post.get("data", {})
                            title = pdata.get("title", "")
                            score = pdata.get("score", 0)
                            cat = "technology" if sub == "technology" else "science" if sub == "science" else "world_news"
                            topics.append({
                                "title": title if "?" in title else f"Why: {title}",
                                "category": cat,
                                "source": f"reddit/{sub}",
                                "trend_score": min(95, max(55, int(score / 500))),
                                "raw_data": {"subreddit": sub, "score": score, "url": pdata.get("url", "")}
                            })
                except Exception as e:
                    logger.warning(f"Reddit {sub} failed: {e}")
        return topics
    except Exception as e:
        logger.error(f"Reddit fetch failed: {e}")
    return []


def get_seed_topics() -> list:
    """Return seed topics for initial app population."""
    return [
        {
            "title": "Why Nvidia stock exploded today",
            "category": "finance",
            "source": "seed",
            "trend_score": 94,
        },
        {
            "title": "TikTok ban is actually happening",
            "category": "technology",
            "source": "seed",
            "trend_score": 89,
        },
        {
            "title": "OpenAI launched autonomous agents",
            "category": "ai",
            "source": "seed",
            "trend_score": 82,
        },
        {
            "title": "The Fed just cut rates again",
            "category": "economy",
            "source": "seed",
            "trend_score": 76,
        },
        {
            "title": "EU just fined Apple 2 billion euros",
            "category": "technology",
            "source": "seed",
            "trend_score": 68,
        },
        {
            "title": "Bitcoin hits new all-time high",
            "category": "crypto",
            "source": "seed",
            "trend_score": 91,
        },
        {
            "title": "NASA discovers high potential for life on Europa",
            "category": "science",
            "source": "seed",
            "trend_score": 73,
        },
        {
            "title": "Why is the internet obsessed with the Hawk Tuah girl",
            "category": "internet_culture",
            "source": "seed",
            "trend_score": 85,
        },
    ]


# Seed explanations matching the seed topics
SEED_EXPLANATIONS = {
    "Why Nvidia stock exploded today": {
        "card_1": "Nvidia posted record quarterly earnings, crushing Wall Street estimates.",
        "card_2": "AI chip demand surged as tech companies race to build AI infrastructure.",
        "card_3": "If you own tech stocks or index funds, your portfolio likely jumped. If you work in tech, your industry just got a massive confidence boost.",
        "card_1_detail": "Revenue hit $35.1B — up 122% year-over-year. Data center revenue alone tripled. The stock surged 14% after hours.",
        "card_2_detail": "Every major tech company is buying Nvidia GPUs. Microsoft, Google, and Meta are spending billions on AI data centers.",
        "card_3_detail": "Your retirement fund probably holds Nvidia. Even if you don't trade stocks, this rally affects the tech job market and AI tools you use daily.",
        "category": "finance",
    },
    "TikTok ban is actually happening": {
        "card_1": "The US government passed a law requiring TikTok to be sold or face a ban.",
        "card_2": "National security concerns about Chinese ownership of user data drove the legislation.",
        "card_3": "If you use TikTok, you could lose access. If you're a creator or small business, your audience and income are at risk.",
        "card_1_detail": "The bill was signed into law, giving ByteDance a deadline to divest TikTok's US operations or shut down.",
        "card_2_detail": "Lawmakers argued that ByteDance could be forced to share US user data with the Chinese government under Chinese law.",
        "card_3_detail": "Your saved content, followers, and shopping habits on TikTok could vanish. Start backing up your content and diversifying to other platforms now.",
        "category": "technology",
    },
    "OpenAI launched autonomous agents": {
        "card_1": "OpenAI released AI agents that can browse the web, write code, and complete tasks independently.",
        "card_2": "Advances in reasoning models made it possible for AI to plan and execute multi-step tasks.",
        "card_3": "Your job could change significantly. Tasks you spend hours on — research, emails, scheduling — could soon be done by AI in minutes.",
        "card_1_detail": "The agents can operate a computer, navigate websites, and make decisions without human guidance.",
        "card_2_detail": "OpenAI's latest models can break down complex goals into steps and self-correct when things go wrong.",
        "card_3_detail": "Whether you're a developer, marketer, or student, AI agents will reshape how you work. Learning to direct AI is becoming a critical skill for your career.",
        "category": "ai",
    },
    "The Fed just cut rates again": {
        "card_1": "The Federal Reserve lowered interest rates by 0.25%, the third cut this cycle.",
        "card_2": "Inflation has cooled enough for the Fed to ease monetary policy.",
        "card_3": "Your mortgage, car loan, and credit card rates are about to get cheaper. If you're saving to buy a home, your window is opening.",
        "card_1_detail": "The benchmark rate now sits at its lowest level in over a year. Markets had widely expected the move.",
        "card_2_detail": "After aggressive rate hikes to fight inflation, prices have stabilized near the Fed's 2% target.",
        "card_3_detail": "Your savings account interest will drop, but borrowing gets cheaper. If you've been waiting to refinance or make a big purchase, now is the time to act.",
        "category": "economy",
    },
    "EU just fined Apple 2 billion euros": {
        "card_1": "The European Commission fined Apple over anti-competitive practices in its App Store.",
        "card_2": "Apple was found to have blocked music streaming apps from telling users about cheaper alternatives.",
        "card_3": "You've been overpaying for app subscriptions. This ruling could mean cheaper prices and more payment options on your iPhone.",
        "card_1_detail": "The fine came after a complaint from Spotify. Apple prevented apps from linking to external payment options.",
        "card_2_detail": "Apple's 30% commission on in-app purchases has been a long-standing grievance for developers worldwide.",
        "card_3_detail": "Your Spotify, Netflix, and other subscriptions may soon offer cheaper direct payment options. Apple's walled garden is cracking open, and your wallet benefits.",
        "category": "technology",
    },
    "Bitcoin hits new all-time high": {
        "card_1": "Bitcoin surpassed its previous record, driven by institutional buying and ETF inflows.",
        "card_2": "Spot Bitcoin ETFs opened the floodgates for traditional investors to buy crypto easily.",
        "card_3": "If you hold Bitcoin, you're in profit. If you don't, you're watching your purchasing power erode against a new asset class.",
        "card_1_detail": "The price broke through previous resistance levels with massive trading volume across all major exchanges.",
        "card_2_detail": "BlackRock, Fidelity, and other giants launched Bitcoin ETFs, making it as easy to buy as a stock.",
        "card_3_detail": "Your retirement fund may already have Bitcoin exposure through ETFs. Understanding crypto is no longer optional — it's part of your financial literacy.",
        "category": "crypto",
    },
    "NASA discovers high potential for life on Europa": {
        "card_1": "NASA's Europa Clipper mission detected strong evidence of a subsurface ocean with organic molecules.",
        "card_2": "Jupiter's moon Europa has the key ingredients for life: water, energy, and organic chemistry.",
        "card_3": "Your understanding of life in the universe might be about to change forever. This could be the biggest scientific discovery of your lifetime.",
        "card_1_detail": "The spacecraft's instruments detected plumes of water vapor containing amino acid precursors.",
        "card_2_detail": "Tidal heating from Jupiter keeps Europa's ocean liquid beneath miles of ice, creating potential habitable zones.",
        "card_3_detail": "If confirmed, this reshapes everything — from your philosophy about humanity's place in the cosmos to how governments fund space exploration with your tax dollars.",
        "category": "science",
    },
    "Why is the internet obsessed with the Hawk Tuah girl": {
        "card_1": "A street interview clip went mega-viral for its unexpected and hilarious answer.",
        "card_2": "The internet's algorithm-driven culture can turn anyone into an overnight sensation.",
        "card_3": "Your next viral moment could be one clip away. This shows how the algorithm can change anyone's life overnight — including yours.",
        "card_1_detail": "The clip was shared millions of times across TikTok, X, and Instagram within 48 hours.",
        "card_2_detail": "Short-form video platforms amplify shocking or funny content exponentially. The clip hit every recommendation algorithm.",
        "card_3_detail": "Your online presence matters more than ever. One candid moment can launch a career or haunt you forever. Be mindful of what you say on camera.",
        "category": "internet_culture",
    },
}


async def collect_all_trending() -> list:
    """Collect trending topics from all available sources."""
    all_topics = []

    # Try each source, don't fail if one source is down
    sources = [
        ("CoinGecko", fetch_coingecko_trending),
        ("Wikipedia", fetch_wikipedia_trending),
        ("Reddit", fetch_reddit_trending),
    ]

    for name, fetcher in sources:
        try:
            topics = await fetcher()
            logger.info(f"Fetched {len(topics)} topics from {name}")
            all_topics.extend(topics)
        except Exception as e:
            logger.warning(f"Failed to fetch from {name}: {e}")

    return all_topics
