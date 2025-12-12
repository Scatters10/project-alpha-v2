# BTC Only Configuration

The bot is now configured to **only trade BTC Up/Down 15-minute contracts**.

## Configuration

### Default Behavior
- **Symbols:** BTC only
- **Markets:** Only BTC Up/Down 15-minute contracts

### To Change (if needed)

**Option 1: Environment Variable**
```powershell
$env:MARKETS="BTC"
python gabagool.py
```

**Option 2: .env File**
Add to `gabagool/.env`:
```env
MARKETS=BTC
```

**Option 3: Multiple Symbols (if you change your mind)**
```env
MARKETS=BTC,ETH
```

## What This Means

✅ **Bot will:**
- Only discover BTC 15-minute markets
- Only subscribe to BTC token price feeds
- Only analyze BTC arbitrage opportunities
- Only trade BTC contracts

❌ **Bot will NOT:**
- Monitor ETH, SOL, XRP, or other symbols
- Waste resources on unused markets
- Clutter dashboard with other symbols

## Benefits

1. **Focused Trading** - All attention on BTC
2. **Faster Processing** - Less markets to monitor
3. **Cleaner Dashboard** - Only BTC data shown
4. **Easier Debugging** - Single market to track

## Verification

When bot starts, you should see:
```
Symbols: BTC
```

And in logs:
```
[BTC] btc-updown-15m-{timestamp}
```

Dashboard will only show BTC market prices and positions.

