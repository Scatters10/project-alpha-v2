# Recommended Approach: Time-Based Imbalance Threshold

## What I Would Do

### 1. **Implement Time-Based Threshold** (Most Important)

The imbalance threshold should be **context-aware** - stricter after startup, more lenient during initial trading.

### 2. **Actually Use the Check** (Currently Unused)

The `_can_buy()` function exists but is never called. We should use it, but make it smart.

### 3. **Keep It Lenient** (Don't Over-Restrict)

The goal is safety, not perfection. Allow natural trading flow while preventing extreme imbalances.

---

## Implementation

### Modified `_can_buy()` Function:

```python
def _can_buy(self, pos: Position, side: str, market_start_time: float = None) -> bool:
    """
    Check if we can buy more of a side, considering imbalance.
    More lenient at startup, stricter after initial period.
    """
    # Calculate time from market start (if available)
    minutes_from_start = 0
    if market_start_time:
        minutes_from_start = (time.time() - market_start_time) / 60.0
    
    # Time-based threshold: very lenient at startup
    if minutes_from_start < 1.0:
        # First minute: allow up to 10x imbalance (startup period)
        max_ratio = 10.0
    elif minutes_from_start < 2.0:
        # Second minute: allow up to 3x imbalance (rebalancing period)
        max_ratio = 3.0
    else:
        # After 2 minutes: use configured threshold (steady-state)
        max_ratio = self.config.max_imbalance_ratio  # 1.3
    
    if side == 'YES':
        if pos.yes_shares == 0:
            return True  # Always allow first position
        if pos.no_shares == 0:
            # If we have no NO shares, limit YES to half max position
            return pos.yes_shares < self.config.max_position_usd / 2
        return pos.yes_shares <= pos.no_shares * max_ratio
    else:  # NO
        if pos.no_shares == 0:
            return True  # Always allow first position
        if pos.yes_shares == 0:
            return pos.no_shares < self.config.max_position_usd / 2
        return pos.no_shares <= pos.yes_shares * max_ratio
```

### Modified `analyze()` Function:

```python
async def analyze(self, market_id: str, recv_time: float):
    pos = self.positions.get(market_id)
    if not pos:
        return
    
    # ... existing orderbook checks ...
    
    # NEW: Check if we can buy (imbalance check)
    # Get market start time from market data
    market_start_time = self.active_markets.get(market_id, {}).get('start_time')
    
    if not self._can_buy(pos, 'YES', market_start_time) or \
       not self._can_buy(pos, 'NO', market_start_time):
        # Skip if we're too imbalanced (but threshold is lenient at startup)
        return
    
    # ... rest of existing logic ...
```

---

## Why This Approach?

### ✅ **Benefits:**

1. **Safety**: Prevents extreme imbalances (like 12x) after startup period
2. **Flexibility**: Allows natural startup imbalance (first 1-2 minutes)
3. **Practical**: Doesn't block legitimate opportunities
4. **Clear Intent**: Code documents the strategy

### ⚠️ **Considerations:**

1. **Need Market Start Time**: Must track when market started
2. **Slight Complexity**: Adds one more check
3. **May Skip Some Trades**: But only when truly imbalanced

---

## Alternative: Simpler Approach

If you want to keep it simple:

### **Just Remove the Unused Code**

```python
# Delete _can_buy() function entirely
# Delete max_imbalance_ratio from config
# Rely on natural rebalancing
```

**Pros:**
- Simpler code
- Current strategy works fine
- No risk of over-restricting

**Cons:**
- No safety net for edge cases
- Could theoretically get stuck imbalanced

---

## My Final Recommendation

**Implement the time-based threshold** because:

1. **Low Risk, High Reward**: Adds safety without blocking opportunities
2. **Addresses Your Concern**: Allows startup imbalance, prevents later imbalance
3. **Future-Proof**: Protects against edge cases
4. **Clear Intent**: Documents that startup imbalance is expected

**But make it VERY lenient:**
- First minute: 10x allowed (covers observed 12x spike)
- Second minute: 3x allowed (covers rebalancing)
- After 2 minutes: 1.3x (steady-state safety)

This way:
- ✅ Startup imbalance is allowed (as it should be)
- ✅ Extreme imbalances are prevented after startup
- ✅ Natural trading flow continues
- ✅ Code is clear about the strategy

---

## Implementation Priority

1. **High Priority**: Add time-based threshold check
2. **Medium Priority**: Track market start time
3. **Low Priority**: Fine-tune the ratios based on more data

The current strategy works, but adding this check makes it more robust and documents the expected behavior.

