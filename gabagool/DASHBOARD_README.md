# Real-Time Dashboard for Gabagool Bot

A beautiful web dashboard that shows live trading activity, positions, and statistics.

## Features

✅ **Real-Time Updates** - Auto-refreshes every 5 seconds  
✅ **Live Trades** - See trades as they happen  
✅ **Position Tracking** - Monitor all active positions  
✅ **Statistics** - Total trades, profit, fill rates  
✅ **Imbalance Monitoring** - See imbalance ratios for each position  
✅ **Beautiful UI** - Modern, responsive design  

## Quick Start

### 1. Install Dependencies

```bash
pip install flask flask-cors
```

Or:
```bash
pip install -r requirements_dashboard.txt
```

### 2. Run the Dashboard

**In a separate terminal window:**

```bash
cd gabagool
python dashboard.py
```

### 3. Open in Browser

Navigate to: **http://localhost:5000**

## Running Bot + Dashboard Together

### Terminal 1: Run the Bot
```bash
cd gabagool
$env:SIMULATION_MODE="true"
python gabagool.py
```

### Terminal 2: Run the Dashboard
```bash
cd gabagool
python dashboard.py
```

Then open **http://localhost:5000** in your browser.

## What You'll See

### Statistics Cards
- Total Trades
- Total Spent
- Guaranteed Profit
- Active Positions
- Opportunities Found
- Fill Rate

### Active Positions
For each market, you'll see:
- YES Shares
- NO Shares
- Total Cost
- Combined Price
- Guaranteed Profit
- Imbalance Ratio

### Recent Trades Table
- Timestamp
- Symbol
- Side (YES/NO)
- Price
- Shares
- Cost
- Combined Price
- Profit
- Latency

## API Endpoint

You can also get JSON data at:
```
http://localhost:5000/api/data
```

Returns:
```json
{
  "stats": {...},
  "positions": {...},
  "recent_trades": [...],
  "timestamp": "..."
}
```

## Notes

- The dashboard reads from `gabagool_ultra.db` (created by the bot)
- Updates automatically every 5 seconds
- Works with both simulation and production mode
- No configuration needed - just run it!

## Troubleshooting

**Dashboard shows "No active positions":**
- Make sure the bot is running and has made at least one trade
- Check that `gabagool_ultra.db` exists in the `gabagool/` directory

**Port 5000 already in use:**
- Change the port in `dashboard.py`: `app.run(port=5001)`

**No data showing:**
- Ensure the bot has been running and saving trades
- Check database file exists and has data

