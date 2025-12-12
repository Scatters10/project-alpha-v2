# Time-Based Imbalance Threshold - Changes Applied ✅

## Summary

All changes have been successfully applied to `gabagool/gabagool.py`.

---

## Changes Made

### 1. Market Start Time Tracking
**Location**: `fetch_markets()` function (lines ~372-384)

**Change**: Extract and store market start time from slug
```python
# Extract market start time from slug (e.g., "btc-updown-15m-1765548000")
market_start_time = None
if 'slug' in market:
    try:
        slug_parts = market['slug'].split('-')
        if len(slug_parts) >= 4:
            timestamp_str = slug_parts[-1]
            market_start_time = int(timestamp_str)
    except (ValueError, IndexError):
        pass

market['start_time'] = market_start_time
```

### 2. Enhanced `_can_buy()` Function
**Location**: Lines 624-651

**Changes**:
- Added `minutes_from_start` parameter
- Implemented time-based threshold logic

**Thresholds**:
```python
First minute (< 1.0 min):  12.0x  # Very lenient for startup
Second minute (1.0-2.0 min): 3.0x  # Moderate for rebalancing
After 2 minutes:             1.3x  # Steady-state safety
```

### 3. Imbalance Check in `analyze()`
**Location**: Lines ~554-567

**Change**: Calculate minutes from start and call `_can_buy()` for both sides
```python
# Imbalance check - time-based threshold (lenient at startup, stricter later)
market_data = self.active_markets.get(market_id, {})
market_start_time = market_data.get('start_time')
minutes_from_start = None
if market_start_time:
    minutes_from_start = (time.time() - market_start_time) / 60.0

# Check if we can buy both sides (considering current imbalance)
can_buy_yes = self._can_buy(pos, 'YES', minutes_from_start)
can_buy_no = self._can_buy(pos, 'NO', minutes_from_start)

if not can_buy_yes or not can_buy_no:
    # Skip if we're too imbalanced (threshold is lenient at startup)
    return
```

---

## Threshold Rationale

### First Minute: 12.0x
- **Observed max**: 12.0x (9:15-9:30 market)
- **Observed range**: 1.86x - 12.0x across all markets
- **Duration**: Very brief (resolves in 0.3-0.57 minutes)
- **Rationale**: Allows natural startup behavior while preventing extreme imbalances

### Second Minute: 3.0x
- **Observed max**: 4.0x (but resolved in first minute)
- **Rationale**: Safety net for edge cases, though all imbalances resolved within first minute

### After 2 Minutes: 1.3x
- **Config value**: From `max_imbalance_ratio` in config
- **Rationale**: Steady-state safety to prevent sustained imbalance

---

## Benefits

1. ✅ **Allows Startup Imbalance**: First minute is lenient (12.0x)
2. ✅ **Prevents Extreme Imbalances**: After 2 minutes, enforces 1.3x limit
3. ✅ **Natural Rebalancing**: Second minute allows 3.0x for catch-up
4. ✅ **Data-Driven**: Based on analysis of 4 markets
5. ✅ **Safety Net**: Protects against edge cases without blocking normal trading

---

## Testing Recommendations

1. **Monitor Logs**: Watch for "Skipping trade: imbalance ratio" messages
2. **Check Behavior**: Verify startup imbalance still works (first minute)
3. **Verify Safety**: Confirm extreme imbalances are prevented after 2 minutes
4. **Compare Performance**: See if this affects fill rates or opportunities

---

## Status

✅ **All changes applied and ready for testing**

The bot will now:
- Allow up to 12.0x imbalance in the first minute (startup period)
- Allow up to 3.0x imbalance in the second minute (rebalancing)
- Enforce 1.3x imbalance limit after 2 minutes (steady-state)

