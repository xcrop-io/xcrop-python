# XCROP Python SDK

Official Python client for the [XCROP API](https://xcrop.io) — X/Twitter data intelligence platform. 39 endpoints covering profile lookup, timelines, search, lists, communities, account monitoring, write operations, and interaction/eligibility checks.

## Installation

```bash
pip install xcrop
```

## Quick Start

```python
from xcrop import XCropClient

client = XCropClient(api_key="xc_live_...")

# Get user profile
user = client.users.get("elonmusk")
print(user["data"]["name"])

# Get user tweets
tweets = client.users.tweets("elonmusk", count=50)
for tweet in tweets["data"]:
    print(tweet["text"])
```

## Features

- **Sync & Async** — `XCropClient` (sync) and `AsyncXCropClient` (async) with identical APIs
- **Auto-retry** — Exponential backoff on 429 (rate limit) and 5xx errors, up to 3 retries
- **Auto-pagination** — `.paginate()` iterators handle cursor-based pagination automatically
- **SSE Streaming** — Real-time search streaming and event streams
- **Type hints** — Full typing for IDE autocomplete
- **Custom exceptions** — `AuthError`, `RateLimitError`, `NotFoundError`, `ServerError`

## Usage

### Users

```python
# Profile
user = client.users.get("elonmusk")

# Tweets, followers, following, etc.
tweets = client.users.tweets("elonmusk", count=20)
followers = client.users.followers("elonmusk", count=50)
following = client.users.following("elonmusk")
mentions = client.users.mentions("elonmusk")
replies = client.users.replies("elonmusk")
media = client.users.media("elonmusk")
verified = client.users.verified_followers("elonmusk")

# Bulk follower IDs (up to 5,000 per call, no profile metadata)
ids = client.users.followers_ids("elonmusk", count=5000)

# Auto-paginate (fetches all pages, yields individual items)
for tweet in client.users.tweets.paginate("elonmusk", count=200):
    print(tweet["text"])

# Batch lookup (up to 100)
users = client.users.batch(["elonmusk", "jack", "vaboronin"])

# Follow relationship check — does `source` follow `target`?
rel = client.users.check_follow(source="jack", target="elonmusk")
print(rel["data"]["source_follows_target"])

# Eligibility checks (for giveaway/airdrop gating)
account_ok = client.users.check_qualified_account(
    "elonmusk", min_followers=100, min_age_days=30,
)
name_ok = client.users.check_qualified_name(
    "elonmusk", contains="Musk", position="anywhere",
)

# Follow / unfollow (requires connected account)
client.users.follow("jack")
client.users.unfollow("jack")
```

### Tweets

```python
# Single tweet
tweet = client.tweets.get("1234567890")

# Conversation thread
conv = client.tweets.conversation("1234567890", count=50)

# Quotes (with pagination)
for quote in client.tweets.quotes.paginate("1234567890", count=100):
    print(quote["text"])

# Batch lookup
tweets = client.tweets.batch(["123", "456", "789"])

# Write operations (requires connected account)
result = client.tweets.create(text="Hello from XCROP SDK!")
client.tweets.reply(tweet_id="1234567890", text="Great thread!")
client.tweets.quote(tweet_id="1234567890", text="Interesting take")
client.tweets.delete(tweet_id="1234567890")

# Like / unlike / retweet / unretweet
client.tweets.like("1234567890")
client.tweets.unlike("1234567890")
client.tweets.retweet("1234567890")
client.tweets.unretweet("1234567890")

# Interaction checks (no connected account needed)
check = client.tweets.check_retweet("1234567890", username="jack")
print(check["data"]["result"])  # True/False

# check_reply / check_quote also accept an optional min_tags (0-20)
check = client.tweets.check_reply("1234567890", username="jack", min_tags=1)
```

### Search

```python
# Basic search
results = client.search.tweets(query="bitcoin", count=50)

# Advanced search
results = client.search.tweets(
    query="ethereum",
    sort="popular",
    lang="en",
    min_likes=100,
    exclude_replies=True,
    since="2024-01-01",
)

# Auto-paginate search
for tweet in client.search.tweets_paginate(query="bitcoin", count=200, sort="latest"):
    print(tweet["text"])

# SSE streaming search
for tweet in client.search.tweets_stream(query="breaking", count=100):
    print(tweet)

# User search
users = client.search.users(query="crypto trader", count=20)
```

### Lists

```python
tweets = client.lists.tweets("1234567890", count=50)
members = client.lists.members("1234567890")
subscribers = client.lists.subscribers("1234567890")

# Paginate
for tweet in client.lists.tweets.paginate("1234567890", count=200):
    print(tweet["text"])
```

### Trending

```python
trending = client.trending.get()
for topic in trending["data"]:
    print(topic["name"], topic.get("tweet_count"))
```

### Communities (beta)

> Communities endpoints are still rolling out and may return a `503`
> (`ServerError`) while the underlying data source stabilizes.

```python
from xcrop import ServerError

try:
    community = client.communities.get("1708766018985501165")
    tweets = client.communities.tweets("1708766018985501165", count=50)
    members = client.communities.members("1708766018985501165", count=50)

    for tweet in client.communities.tweets.paginate("1708766018985501165", count=200):
        print(tweet["text"])
except ServerError:
    print("Communities data source temporarily unavailable")
```

### Account Management

```python
# Connect via credentials
client.account.connect(username="myuser", password="mypass", totp_secret="TOTP_SECRET")

# Connect via cookies
client.account.connect(cookies={"auth_token": "...", "ct0": "..."})

# Check status
status = client.account.status()
print(status["data"]["connected"])

# Disconnect
client.account.disconnect()
```

### Real-time Stream

```python
for event in client.stream.connect():
    print(event)
```

## Async Usage

```python
import asyncio
from xcrop import AsyncXCropClient

async def main():
    async with AsyncXCropClient(api_key="xc_live_...") as client:
        # All methods are async
        user = await client.users.get("elonmusk")
        print(user["data"]["name"])

        # Async pagination
        async for tweet in client.users.tweets.paginate("elonmusk", count=200):
            print(tweet["text"])

        # Async search streaming
        async for tweet in client.search.tweets_stream(query="breaking"):
            print(tweet)

asyncio.run(main())
```

## Error Handling

```python
from xcrop import XCropClient, AuthError, RateLimitError, NotFoundError, XCropError

client = XCropClient(api_key="xc_live_...")

try:
    user = client.users.get("nonexistent_user_12345")
except NotFoundError:
    print("User not found")
except AuthError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}s")
except XCropError as e:
    print(f"API error: {e.message} (HTTP {e.status_code})")
```

## Configuration

```python
client = XCropClient(
    api_key="xc_live_...",
    base_url="https://xcrop.io/api/v2",  # default
    timeout=30.0,                          # seconds, default
    max_retries=3,                         # default
)
```

You can also pass a custom `httpx.Client` or `httpx.AsyncClient`:

```python
import httpx

http = httpx.Client(proxy="http://proxy:8080")
client = XCropClient(api_key="xc_live_...", http_client=http)
```

## Rate Limits & Plans

Per-minute request limits are enforced per plan (in addition to the monthly
credit allowance):

| Plan    | Requests / min |
|---------|-----------------|
| Starter | 60              |
| Basic   | 300             |
| Pro     | 600             |
| PAYG    | 300             |

Exceeding the limit raises `RateLimitError` (the SDK auto-retries 429s with
backoff before raising). See [xcrop.io/pricing](https://xcrop.io/pricing) for
credit costs per endpoint.

## Billing

Plans and credit top-ups are paid via cryptocurrency: **USDT (BEP-20)**,
**USDC (BEP-20)**, **SOL**, and **POL**. Credit card payments via Stripe are
coming soon. See [xcrop.io/pricing](https://xcrop.io/pricing) and the
dashboard billing page to manage your subscription.

## API Response Format

All methods return the raw API response as a dict:

```python
{
    "data": ...,          # Response payload
    "meta": {
        "latency_ms": 123,
        "cached": True,
        "total": 50,
        "cursor": "abc123",
        "has_next": True,
    }
}
```

## Requirements

- Python 3.8+
- httpx >= 0.24.0

## License

MIT
