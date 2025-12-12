#!/usr/bin/env python3
"""
Monitor bot for next 15-minute market slot
"""

import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

def get_next_slot_time():
    """Calculate next 15-minute slot"""
    now = datetime.now(ZoneInfo('America/New_York'))
    current_min = now.minute
    next_slot_min = ((current_min // 15) + 1) * 15
    if next_slot_min >= 60:
        next_slot_min = 0
        next_hour = (now.hour + 1) % 24
    else:
        next_hour = now.hour
    next_time = now.replace(hour=next_hour, minute=next_slot_min, second=0, microsecond=0)
    return next_time

def monitor_bot():
    """Monitor bot state and wait for next market"""
    next_slot = get_next_slot_time()
    now = datetime.now(ZoneInfo('America/New_York'))
    
    print("=" * 70)
    print("🔍 Monitoring Bot for Next Market Slot")
    print("=" * 70)
    print(f"Current Time: {now.strftime('%I:%M:%S %p %Z')}")
    print(f"Next Market Slot: {next_slot.strftime('%I:%M:%S %p %Z')}")
    
    wait_seconds = (next_slot - now).total_seconds()
    print(f"Time Until Next Slot: {int(wait_seconds // 60)}m {int(wait_seconds % 60)}s")
    print("=" * 70)
    print("\nMonitoring bot state... (Press Ctrl+C to stop)\n")
    
    last_messages = 0
    last_market_count = 0
    
    try:
        while True:
            try:
                with open('gabagool_state.json', 'r') as f:
                    state = json.load(f)
                
                wss_connected = state.get('wss_connected', False)
                messages = state.get('wss_messages', 0)
                market_count = len(state.get('active_markets', {}))
                
                # Check for new messages
                if messages > last_messages:
                    msg_diff = messages - last_messages
                    print(f"✅ {datetime.now().strftime('%H:%M:%S')} - Received {msg_diff} new messages (Total: {messages})")
                    last_messages = messages
                
                # Check for new markets
                if market_count > last_market_count:
                    print(f"🆕 {datetime.now().strftime('%H:%M:%S')} - New market discovered! (Total: {market_count})")
                    last_market_count = market_count
                    
                    # Show market details
                    for market_id, market in state.get('active_markets', {}).items():
                        if market.get('has_data'):
                            print(f"   📊 {market.get('symbol')} - YES: ${market.get('yes_price')} NO: ${market.get('no_price')}")
                
                # Check for price updates
                for market_id, market in state.get('active_markets', {}).items():
                    if market.get('has_data') and market.get('yes_price'):
                        print(f"💰 {datetime.now().strftime('%H:%M:%S')} - {market.get('symbol')} Prices: YES=${market.get('yes_price')} NO=${market.get('no_price')} Combined={market.get('combined_price')}")
                        break
                
                # Status update every 30 seconds
                if int(time.time()) % 30 == 0:
                    status = "🟢 Connected" if wss_connected else "🔴 Disconnected"
                    print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - Status: {status} | Messages: {messages} | Markets: {market_count}")
                
            except FileNotFoundError:
                print(f"⏳ {datetime.now().strftime('%H:%M:%S')} - Waiting for bot to create state file...")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

if __name__ == "__main__":
    monitor_bot()

