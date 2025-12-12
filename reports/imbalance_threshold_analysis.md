# Imbalance Threshold Analysis - All Markets

## Observed Data Summary

### Market 1: 9:15-9:30
- **Max Imbalance**: 12.0x (at 0.533 min)
- **Balance Achieved**: 0.567 min (trade #8)
- **First Trade**: YES side
- **Times Exceeded 1.3x**: 24 times

### Market 2: 9:30-9:45
- **Max Imbalance**: 4.0x (at 0.367 min)
- **Balance Achieved**: 0.333 min (trade #2)
- **First Trade**: YES side
- **Times Exceeded 1.3x**: 15 times

### Market 3: 10:00-10:15
- **Max Imbalance**: 3.0x (at 0.300 min)
- **Balance Achieved**: 0.300 min (trade #2)
- **First Trade**: NO side
- **Times Exceeded 1.3x**: 15 times

### Market 4: 10:30-10:45
- **Max Imbalance**: 1.86x (at 0.633 min)
- **Balance Achieved**: 0.500 min (trade #5)
- **First Trade**: YES side
- **Times Exceeded 1.3x**: 32 times

---

## Current Implementation

```python
# First minute: 10.0x threshold
# Second minute: 3.0x threshold
# After 2 minutes: 1.3x threshold
```

---

## Analysis

### Key Findings:

1. **Max Imbalance Range**: 1.86x to 12.0x
   - One market (9:15-9:30) exceeded our 10.0x threshold
   - All others were within 10.0x

2. **Balance Achievement**: Very fast
   - All markets balanced within 0.3-0.57 minutes
   - Well within first minute

3. **Imbalance Duration**: Brief spikes
   - Imbalances are temporary and resolve quickly
   - No sustained high imbalance

4. **Pattern Consistency**: 
   - All imbalances occur in first minute
   - Balance achieved quickly (2-8 trades)

---

## Recommendations

### Option 1: Increase First Minute Threshold (Conservative)
```python
if minutes_from_start < 1.0:
    max_ratio = 15.0  # Increased from 10.0 to cover observed 12.0x
```

**Pros:**
- Covers all observed imbalances
- Very safe margin

**Cons:**
- Allows very high imbalance (though brief)

### Option 2: Keep Current (10.0x) - Recommended
```python
if minutes_from_start < 1.0:
    max_ratio = 10.0  # Current
```

**Pros:**
- Covers 3 out of 4 markets perfectly
- The 12.0x was a brief spike that resolved in 0.034 min
- Prevents extreme imbalances

**Cons:**
- Would have blocked some trades in 9:15-9:30 market
- But those trades were part of a brief spike

### Option 3: Make Second Minute More Lenient
```python
elif minutes_from_start < 2.0:
    max_ratio = 4.0  # Increased from 3.0 to match observed max
```

**Pros:**
- Matches observed 4.0x in one market
- Still provides safety

**Cons:**
- All imbalances resolved within first minute anyway
- May not be necessary

---

## Final Recommendation

**Keep current thresholds with one small adjustment:**

```python
if minutes_from_start < 1.0:
    max_ratio = 12.0  # Slightly increase to cover observed max
elif minutes_from_start < 2.0:
    max_ratio = 3.0   # Keep current
else:
    max_ratio = self.config.max_imbalance_ratio  # 1.3
```

**Rationale:**
1. **12.0x covers all observed cases** - including the one outlier
2. **Still very restrictive** - prevents truly extreme imbalances
3. **Balance is achieved quickly** - so high threshold is only for brief period
4. **Safety margin** - 12.0x is still reasonable for startup period

**Alternative (if you want to be more conservative):**
- Keep 10.0x and accept that one market had a brief spike
- The spike resolved in 0.034 minutes, so impact is minimal

---

## Conclusion

The current implementation is **very close to optimal**. The only change I'd consider is increasing the first-minute threshold from 10.0x to 12.0x to cover the observed maximum, but this is optional since:

1. The 12.0x spike was extremely brief (0.034 min)
2. Balance was achieved quickly
3. All other markets were well within 10.0x

**My recommendation: Keep 10.0x or increase to 12.0x - both are reasonable choices.**

