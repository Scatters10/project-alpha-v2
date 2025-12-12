# Time-Based Imbalance Threshold Implementation

## Changes Made to gabagool.py

### 1. **Track Market Start Time**

**Location**: `fetch_markets()` function

**Change**: Extract timestamp from market slug and store it in market data
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

### 2. **Enhanced `_can_buy()` Function**

**Location**: Line ~586

**Changes**:
- Added `minutes_from_start` parameter
- Implemented time-based threshold logic:
  - **First minute**: 10.0x (very lenient - allows startup imbalance)
  - **Second minute**: 3.0x (moderate - allows rebalancing)
  - **After 2 minutes**: 1.3x (steady-state safety)

**New Logic**:
```python
def _can_buy(self, pos: Position, side: str, minutes_from_start: float = None) -> bool:
    # Determine threshold based on time from market start
    if minutes_from_start is None or minutes_from_start < 1.0:
        max_ratio = 10.0  # Very lenient in first minute
    elif minutes_from_start < 2.0:
        max_ratio = 3.0   # Moderate in second minute
    else:
        max_ratio = self.config.max_imbalance_ratio  # 1.3 after 2 minutes
    # ... rest of logic
```

### 3. **Added Imbalance Check in `analyze()`**

**Location**: Line ~554 (after position limit check)

**Change**: Calculate minutes from start and call `_can_buy()` for both sides
```python
# Imbalance check - time-based threshold
market_data = self.active_markets.get(market_id, {})
market_start_time = market_data.get('start_time')
minutes_from_start = None
if market_start_time:
    minutes_from_start = (time.time() - market_start_time) / 60.0

# Check if we can buy both sides
can_buy_yes = self._can_buy(pos, 'YES', minutes_from_start)
can_buy_no = self._can_buy(pos, 'NO', minutes_from_start)

if not can_buy_yes or not can_buy_no:
    # Skip if too imbalanced (with debug logging)
    return
```

---

## How It Works

### Startup Period (0-1 minute):
- **Threshold**: 10.0x imbalance allowed
- **Purpose**: Allows natural startup imbalance (like your observed 12x spike)
- **Result**: Bot can build initial position without restriction

### Rebalancing Period (1-2 minutes):
- **Threshold**: 3.0x imbalance allowed
- **Purpose**: Allows rebalancing as bot catches up on the lagging side
- **Result**: Bot can correct temporary imbalances

### Steady-State (After 2 minutes):
- **Threshold**: 1.3x imbalance (configurable)
- **Purpose**: Prevents extreme imbalances during normal trading
- **Result**: Maintains balanced positions

---

## Benefits

1. ✅ **Allows Startup Imbalance**: First minute is very lenient (10x)
2. ✅ **Prevents Extreme Imbalances**: After 2 minutes, enforces 1.3x limit
3. ✅ **Natural Rebalancing**: Second minute allows 3x for catch-up
4. ✅ **Safety Net**: Protects against edge cases without blocking normal trading
5. ✅ **Clear Intent**: Code documents expected behavior

---

## Testing Recommendations

1. **Monitor Logs**: Watch for "Skipping trade: imbalance ratio" messages
2. **Check Behavior**: Verify startup imbalance still works (first minute)
3. **Verify Safety**: Confirm extreme imbalances are prevented after 2 minutes
4. **Compare Performance**: See if this affects fill rates or opportunities

---

## Configuration

The thresholds are hardcoded but can be made configurable:

```python
# In Config class, could add:
startup_imbalance_ratio: float = 10.0
rebalancing_imbalance_ratio: float = 3.0
startup_period_minutes: float = 1.0
rebalancing_period_minutes: float = 2.0
```

Currently using fixed values for simplicity.

---

## Backward Compatibility

- ✅ **Fully backward compatible**: If `market_start_time` is None, uses lenient threshold
- ✅ **No breaking changes**: Existing functionality preserved
- ✅ **Graceful degradation**: Works even if timestamp extraction fails

---

## Next Steps

1. Test with live trading (or simulation)
2. Monitor if any legitimate trades are being blocked
3. Adjust thresholds if needed based on real-world data
4. Consider making thresholds configurable via .env

