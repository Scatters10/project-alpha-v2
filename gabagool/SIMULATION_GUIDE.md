# Running Gabagool in Simulation Mode

## Quick Start

### Method 1: Environment Variable (Recommended)

**Windows PowerShell:**
```powershell
cd gabagool
$env:SIMULATION_MODE="true"
python gabagool.py
```

**Windows CMD:**
```cmd
cd gabagool
set SIMULATION_MODE=true
python gabagool.py
```

**Linux/Mac:**
```bash
cd gabagool
export SIMULATION_MODE=true
python gabagool.py
```

### Method 2: .env File

Create `gabagool/.env`:
```env
SIMULATION_MODE=true
POLYMARKET_PRIVATE_KEY=your_private_key_here
MARKETS=BTC,ETH,SOL,XRP
MAX_COMBINED_PRICE=0.97
MAX_POSITION_USD=100
MIN_ORDER_USD=5
MAX_ORDER_USD=25
MAX_IMBALANCE_RATIO=1.3
```

Then run:
```bash
python gabagool.py
```

## What Simulation Mode Does

✅ **DOES:**
- Connects to real Polymarket WebSocket
- Receives real-time orderbook data
- Analyzes arbitrage opportunities
- Simulates order execution
- Updates positions in memory
- Logs all trades with `[SIM]` prefix
- Saves trades to database
- Tests your strategy safely

❌ **DOES NOT:**
- Place real orders
- Spend real money
- Execute on-chain transactions
- Risk your funds

## Simulation vs Production

| Feature | Simulation | Production |
|---------|-----------|------------|
| WebSocket Connection | ✅ Real | ✅ Real |
| Market Data | ✅ Real | ✅ Real |
| Order Execution | ❌ Simulated | ✅ Real |
| Position Updates | ✅ In Memory | ✅ On-Chain |
| Risk | ✅ None | ⚠️ Real Money |
| Logging | `[SIM]` prefix | `[PROD]` prefix |

## Verification

When running in simulation mode, you'll see:
```
======================================================================
GABAGOOL ULTRA [🔬 SIMULATION]
======================================================================
  ⚠️  SIMULATION MODE - no real orders will be placed
```

All trade logs will show:
```
[SYMBOL] [SIM] ✓ YES @ 0.5000 x 10.0 = $5.00
```

## Testing Your Strategy

Simulation mode is perfect for:
1. **Testing new thresholds** (like the time-based imbalance we just added)
2. **Validating strategy changes** before risking real money
3. **Analyzing market behavior** without cost
4. **Debugging** order execution logic
5. **Performance testing** under real market conditions

## Switching to Production

When ready for real trading:
```powershell
$env:SIMULATION_MODE="false"
python gabagool.py
```

Or in `.env`:
```env
SIMULATION_MODE=false
```

**⚠️ WARNING:** Make sure you're ready before switching to production mode!

## Current Implementation

The bot now includes:
- ✅ Time-based imbalance thresholds (12.0x / 3.0x / 1.3x)
- ✅ Market start time tracking
- ✅ Imbalance checks before trading
- ✅ Simulation mode support

All ready to test in simulation! 🚀

