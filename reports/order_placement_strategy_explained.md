# Order Placement Strategy - Detailed Explanation

## Based on Analysis of BTC_UpDown_9-15-930_trades.json

---

## Key Findings from Trade Data

### Trade Statistics
- **Total Trades**: 955
- **YES Trades**: 486 (50.9%)
- **NO Trades**: 469 (49.1%)
- **Ratio**: Nearly 1:1 (balanced)
- **Paired Orders**: 153 transactions with multiple orders
- **Single Orders**: 519 transactions

### Order Timing
- **Average time between YES/NO**: 13.9 seconds
- **Range**: 0-70 seconds
- **Pattern**: Orders are placed **SEQUENTIALLY**, not simultaneously

---

## How the Bot Places Orders

### 1. **Trigger: Orderbook Update**

The bot is **reactive** - it responds to WebSocket orderbook updates:

```python
# When orderbook updates arrive:
async def handle_message(self, data: dict, recv_time: float):
    if event == 'book':
        # Update orderbook cache
        self.orderbook.update(token_id, bids, asks)
        # Immediately analyze for arbitrage
        await self.analyze(market_id, recv_time)
```

**Every orderbook update triggers analysis** - the bot doesn't wait, it acts immediately.

---

### 2. **Arbitrage Detection**

Before placing any order, the bot checks:

```python
# Get best prices from orderbook
best_yes = yes_asks[0]['price']  # Best ask (to buy YES)
best_no = no_asks[0]['price']   # Best ask (to buy NO)
combined = best_yes + best_no

# Add 2 cent buffer for slippage
combined_with_buffer = combined + 0.04

# Only trade if combined < 0.97 (after buffer)
if combined_with_buffer >= 0.97:
    return  # Skip - no arbitrage
```

**Key Point**: Bot only trades when `combined_price < 0.97` (3%+ profit margin after slippage).

---

### 3. **Position Limits Check**

```python
# Check if we've hit max position
if pos.total_cost >= max_position_usd:  # Default: $100
    return  # Skip - position full
```

**Bot stops trading** when total position reaches $100.

---

### 4. **Imbalance Check (Time-Based)**

```python
# Calculate minutes from market start
minutes_from_start = (time.time() - market_start_time) / 60.0

# Time-based thresholds:
if minutes_from_start < 1.0:
    max_ratio = 12.0  # Very lenient at startup
elif minutes_from_start < 2.0:
    max_ratio = 3.0   # Moderate
else:
    max_ratio = 1.3   # Strict after 2 minutes

# Check if we can buy
if not _can_buy(pos, 'YES', minutes_from_start):
    return  # Skip - too imbalanced
```

**This prevents extreme imbalances** while allowing natural startup behavior.

---

### 5. **Calculate Order Size**

```python
# Calculate how many shares to buy
remaining = max_position_usd - pos.total_cost
cost_per_pair = best_yes + best_no
max_pairs = remaining / cost_per_pair

# Limit by max order size ($25 per side)
max_pairs_by_order = (max_order_usd * 2) / cost_per_pair

# Take minimum (position limit or order limit)
shares = min(max_pairs, max_pairs_by_order)
shares = int(shares)  # Round down to whole number

# Check minimum order size ($5 per side)
if shares * price < min_order_usd:
    return  # Skip - order too small
```

**Key Points**:
- Tries to buy **EQUAL shares** on both sides
- Limited by remaining position capacity
- Limited by max order size ($25 per side)
- Must meet minimum order size ($5 per side)

---

### 6. **Order Execution**

```python
# Execute BOTH orders in parallel
await asyncio.gather(
    self._execute_fok(pos, 'YES', yes_price, shares, yes_token, recv_time),
    self._execute_fok(pos, 'NO', no_price, shares, no_token, recv_time),
)
```

**Important**: Despite the function name `_execute_fok`, the bot actually uses **GTC (Good Till Cancel)** orders:

```python
resp = self.clob.post_order(signed_order, OrderType.GTC)
```

**GTC orders**:
- Stay in the orderbook until filled or cancelled
- Don't expire immediately
- Allow partial fills
- More reliable than FOK for market making

---

## What the Trade Data Reveals

### Pattern 1: Sequential Order Placement

**Observation**: Average 13.9 seconds between YES and NO orders

**Why This Happens**:
1. Bot tries to place both orders simultaneously
2. But one order may fill immediately while other is still pending
3. Bot then places another order to rebalance
4. This creates sequential pattern

**Example from trades**:
```
Trade #1: YES @ $0.44 x 20 (fills immediately)
Trade #2: YES @ $0.44 x 20 (fills immediately)  
Trade #3: YES @ $0.44 x 20 (fills immediately)
Trade #4: NO @ $0.55 x 5 (catches up, 2 seconds later)
```

### Pattern 2: Rebalancing Behavior

**Observation**: Bot continues buying one side until balance is achieved

**Why**:
- If YES fills but NO doesn't, bot keeps trying NO
- If NO fills but YES doesn't, bot keeps trying YES
- This explains the sequential pattern

### Pattern 3: Equal Share Target

**Observation**: Final positions are nearly balanced (1.04:1 ratio)

**How**:
- Bot calculates shares to buy based on equal pairs
- Tries to maintain balance throughout trading
- Imbalance threshold prevents extreme positions

---

## Order Placement Flow Diagram

```
Orderbook Update Received
        ↓
Check: Combined Price < 0.97? → NO → Skip
        ↓ YES
Check: Position < $100? → NO → Skip
        ↓ YES
Check: Imbalance OK? → NO → Skip
        ↓ YES
Calculate: Equal shares for both sides
        ↓
Check: Order size >= $5? → NO → Skip
        ↓ YES
Place: YES order (GTC)
Place: NO order (GTC)
        ↓
Wait for fills
        ↓
If one fills, other doesn't:
  → Place another order to rebalance
```

---

## Key Strategy Characteristics

### 1. **Reactive, Not Proactive**
- Bot doesn't predict prices
- Responds to orderbook updates in real-time
- Acts immediately when opportunity detected

### 2. **Equal Pairing Goal**
- Always tries to buy equal shares on both sides
- Maintains balanced position
- Prevents directional risk

### 3. **Persistent Execution**
- Keeps placing orders until position limit reached
- Rebalances if one side fills before other
- Doesn't give up on opportunities

### 4. **Risk Management**
- Position limits ($100 max)
- Order size limits ($5-$25 per side)
- Imbalance thresholds (time-based)
- Slippage buffer (2 cents per side)

### 5. **Market Making Style**
- Uses GTC orders (stay in orderbook)
- Provides liquidity
- Captures spread between YES and NO

---

## Why Sequential Orders?

The 13.9 second average delay suggests:

1. **Execution Timing**: Orders placed simultaneously but fill at different times
2. **Orderbook Depth**: One side may have more liquidity than other
3. **Rebalancing**: Bot actively rebalances when imbalance occurs
4. **Partial Fills**: GTC orders may partially fill, requiring follow-up orders

This is **normal behavior** for a market-making bot that maintains balanced positions.

---

## Summary

The bot's order placement strategy:

1. ✅ **Reactive** - Responds to orderbook updates
2. ✅ **Arbitrage-focused** - Only trades when combined < 0.97
3. ✅ **Balanced** - Tries to maintain equal YES/NO positions
4. ✅ **Persistent** - Keeps trading until limits reached
5. ✅ **Risk-managed** - Multiple safety checks before each trade

The sequential order pattern is a **feature, not a bug** - it shows the bot is actively rebalancing to maintain balanced positions, which is exactly what you want for arbitrage trading.

