# Polymarket Connection & API Keys

## ✅ WebSocket Data Feed (PUBLIC - No Keys Needed!)

The bot connects to Polymarket's **public WebSocket** for real-time market data:

```
wss://ws-subscriptions-clob.polymarket.com/ws/market
```

**This is a PUBLIC endpoint** - you do NOT need:
- ❌ API keys
- ❌ API secrets  
- ❌ API passphrases
- ❌ Authentication tokens

**You WILL see live prices** as long as:
- ✅ The bot is running
- ✅ WebSocket connection is established
- ✅ Markets are discovered

## 🔑 POLYMARKET_PRIVATE_KEY (Only for Trading)

The `POLYMARKET_PRIVATE_KEY` in your `.env` file is **ONLY needed for placing orders**.

**It is NOT needed for:**
- ✅ Reading market data
- ✅ Receiving price updates
- ✅ WebSocket connection
- ✅ Viewing orderbooks

**It IS needed for:**
- ⚠️ Placing real orders (production mode)
- ⚠️ CLOB client initialization (but works in simulation without real orders)

## 📊 How to Verify Connection

### 1. Check Dashboard Header
Look for:
- 🟢 **WebSocket: Connected** = Receiving data
- 🔴 **WebSocket: Disconnected** = Not connected

### 2. Check Live Market Prices Section
- ✅ **"Receiving live price updates"** = Prices coming in
- ⚠️ **"Waiting for price data..."** = No prices yet

### 3. Check WebSocket Messages Counter
- If `Messages: 0` = Not receiving data
- If `Messages: 100+` = Receiving data actively

### 4. Check Bot Terminal Output
Look for:
```
WSS connected
Subscribed to X tokens
```

## 🔍 Debugging Connection Issues

### If WebSocket Shows Disconnected:

1. **Check if bot is running:**
   ```powershell
   Get-Process python
   ```

2. **Check bot terminal for errors:**
   - Look for "WSS error" messages
   - Check for connection timeouts

3. **Check network/firewall:**
   - Ensure port 443 (HTTPS/WSS) is not blocked
   - Check if corporate firewall blocks WebSocket connections

4. **Check if markets are discovered:**
   - Bot needs to find active 15-minute markets first
   - Markets refresh every 15 seconds

### If Prices Show "No Data":

1. **Wait a few seconds** - Markets may be discovering
2. **Check if markets exist** - No active 15-min contracts = no data
3. **Check WebSocket status** - Must be connected first
4. **Check bot logs** - Look for subscription messages

## 📈 What the Dashboard Shows

### Live Market Prices Section:
- **YES Price** - Current best ask price for YES side
- **NO Price** - Current best ask price for NO side  
- **Combined Price** - YES + NO (arbitrage opportunity if < 1.0)
- **Arbitrage Margin** - Profit percentage if combined < 1.0
- **Status Indicator** - Green = receiving data, Red = no data

### Connection Status:
- **WebSocket:** 🟢 Connected / 🔴 Disconnected
- **Messages:** Total WebSocket messages received
- **Mode:** 🔬 Simulation / 🚀 Production

## 🎯 Summary

**For Data/Price Updates:**
- ✅ NO API keys needed
- ✅ Public WebSocket connection
- ✅ Works in simulation mode
- ✅ Works without POLYMARKET_PRIVATE_KEY

**For Trading:**
- ⚠️ POLYMARKET_PRIVATE_KEY required
- ⚠️ Only needed in production mode
- ⚠️ Used by CLOB client for order signing

**Your .env file should have:**
```env
POLYMARKET_PRIVATE_KEY=your_key_here  # Only for trading, not for data
SIMULATION_MODE=true                   # Safe testing mode
```

The bot will connect to WebSocket and receive prices **even if POLYMARKET_PRIVATE_KEY is invalid** - it just won't be able to place real orders.

