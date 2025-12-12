# Polymarket Orderbook API Guide

## ✅ Yes, You Can Pull Orderbook Data Directly!

Polymarket provides a **REST API endpoint** to query orderbook data directly from contracts.

## API Endpoint

```
GET https://clob.polymarket.com/book?token_id={token_id}
```

**No authentication required** - This is a public endpoint!

## How to Use

### Method 1: Using the Query Script

```bash
cd gabagool
python query_orderbook.py
```

This will:
- Find the current BTC 15-minute market
- Get token IDs for YES and NO sides
- Query orderbook for both tokens
- Show best bid/ask prices
- Calculate arbitrage opportunities

### Method 2: Query Specific Token

```bash
python query_orderbook.py {token_id}
```

Example:
```bash
python query_orderbook.py 95061850580363759920559683827673129492149838425917049413299372573515654266932
```

### Method 3: Direct API Call

```python
import requests

token_id = "95061850580363759920559683827673129492149838425917049413299372573515654266932"
response = requests.get(
    "https://clob.polymarket.com/book",
    params={"token_id": token_id}
)

orderbook = response.json()
bids = orderbook.get('bids', [])
asks = orderbook.get('asks', [])

best_bid = bids[0] if bids else None
best_ask = asks[0] if asks else None
```

## Response Format

```json
{
  "bids": [
    {"price": "0.50", "size": "100.0"},
    {"price": "0.49", "size": "50.0"}
  ],
  "asks": [
    {"price": "0.51", "size": "75.0"},
    {"price": "0.52", "size": "25.0"}
  ]
}
```

## Getting Token IDs

Token IDs come from the market's `clobTokenIds` field:

```python
import requests

slug = "btc-updown-15m-1765560600"
response = requests.get(f"https://gamma-api.polymarket.com/markets/slug/{slug}")
market = response.json()

token_ids = market.get("clobTokenIds")
yes_token_id = token_ids[0]  # First token is YES
no_token_id = token_ids[1]   # Second token is NO
```

## Use Cases

1. **Real-time Price Checking** - Get current best bid/ask without WebSocket
2. **Arbitrage Detection** - Calculate combined prices instantly
3. **Market Analysis** - Analyze orderbook depth and liquidity
4. **Backup Data Source** - If WebSocket fails, use REST API
5. **Historical Analysis** - Query orderbooks at specific times

## Advantages Over WebSocket

✅ **On-Demand** - Query when needed, no subscription required  
✅ **Simple** - Single HTTP request  
✅ **Reliable** - No connection management  
✅ **Fast** - Get snapshot instantly  

## Disadvantages

❌ **Not Real-Time** - Must poll repeatedly for updates  
❌ **Rate Limits** - May have API rate limits  
❌ **Less Efficient** - WebSocket is better for continuous updates  

## Integration with Bot

The bot currently uses WebSocket for real-time updates, but you could:

1. **Add REST API fallback** - If WebSocket fails, poll REST API
2. **Initial snapshot** - Get orderbook snapshot on startup
3. **Verification** - Cross-check WebSocket data with REST API
4. **Dashboard** - Query orderbook directly for dashboard display

## Example: Add to Dashboard

You could add an API endpoint to the dashboard:

```python
@app.route('/api/orderbook/<token_id>')
def get_orderbook_api(token_id):
    orderbook = get_orderbook(token_id)
    return jsonify(orderbook)
```

Then dashboard can query orderbook directly without waiting for WebSocket updates!

## Summary

**Yes, you can pull orderbook data directly!**

- ✅ REST API endpoint: `GET /book?token_id={token_id}`
- ✅ No authentication needed
- ✅ Works for any token ID
- ✅ Returns bids and asks
- ✅ Perfect for on-demand queries

The bot uses WebSocket for real-time updates, but REST API is great for:
- Initial snapshots
- Fallback when WebSocket fails
- Direct queries from dashboard
- One-off price checks

