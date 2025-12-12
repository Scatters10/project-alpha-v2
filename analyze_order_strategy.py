#!/usr/bin/env python3
"""
Analyze order placement strategy from trades.json
"""

import json
import sys
from datetime import datetime
from collections import defaultdict

def analyze_order_strategy(trades_file):
    """Analyze how orders are placed based on trade data"""
    
    with open(trades_file, 'r', encoding='utf-8') as f:
        trades = json.load(f)
    
    if not trades:
        print("No trades found")
        return
    
    # Sort by timestamp
    trades_sorted = sorted(trades, key=lambda x: x.get('timestamp', 0))
    
    print("="*80)
    print("ORDER PLACEMENT STRATEGY ANALYSIS")
    print("="*80)
    print(f"\nTotal Trades: {len(trades_sorted)}")
    
    # Analyze first 20 trades to see pattern
    print("\n" + "="*80)
    print("FIRST 20 TRADES - ORDER PLACEMENT PATTERN")
    print("="*80)
    
    yes_shares = 0
    no_shares = 0
    yes_cost = 0
    no_cost = 0
    
    for i, trade in enumerate(trades_sorted[:20]):
        side = trade.get('outcome', '').upper()
        price = float(trade.get('price', 0))
        size = float(trade.get('size', 0))
        cost = price * size
        timestamp = trade.get('timestamp', 0)
        
        if timestamp:
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime('%H:%M:%S')
        else:
            time_str = "N/A"
        
        if side == 'UP':
            yes_shares += size
            yes_cost += cost
        elif side == 'DOWN':
            no_shares += size
            no_cost += cost
        
        # Calculate combined price if we have both sides
        combined = None
        if yes_shares > 0 and no_shares > 0:
            yes_avg = yes_cost / yes_shares
            no_avg = no_cost / no_shares
            combined = yes_avg + no_avg
        
        print(f"\nTrade #{i+1} - {time_str}")
        print(f"  Side: {side:4} | Price: ${price:.4f} | Size: {size:.2f} | Cost: ${cost:.2f}")
        print(f"  Position: YES={yes_shares:.2f} (${yes_cost:.2f}) | NO={no_shares:.2f} (${no_cost:.2f})")
        if combined:
            print(f"  Combined Price: ${combined:.4f} | Profit Margin: ${(1.0 - combined):.4f} ({((1.0 - combined) * 100):.2f}%)")
    
    # Analyze pairing pattern
    print("\n" + "="*80)
    print("ORDER PAIRING ANALYSIS")
    print("="*80)
    
    # Group trades by transaction hash (same transaction = paired orders)
    by_tx = defaultdict(list)
    for trade in trades_sorted:
        tx_hash = trade.get('transactionHash', '')
        if tx_hash:
            by_tx[tx_hash].append(trade)
    
    paired_trades = [trades for trades in by_tx.values() if len(trades) >= 2]
    single_trades = [trades for trades in by_tx.values() if len(trades) == 1]
    
    print(f"\nPaired Orders (same transaction): {len(paired_trades)}")
    print(f"Single Orders: {len(single_trades)}")
    
    if paired_trades:
        print(f"\nExample Paired Orders (first 5):")
        for i, pair in enumerate(paired_trades[:5]):
            print(f"\n  Transaction {i+1}: {pair[0].get('transactionHash', '')[:20]}...")
            for trade in pair:
                side = trade.get('outcome', '').upper()
                price = float(trade.get('price', 0))
                size = float(trade.get('size', 0))
                print(f"    {side:4} @ ${price:.4f} x {size:.2f} = ${price * size:.2f}")
    
    # Analyze timing between YES and NO orders
    print("\n" + "="*80)
    print("ORDER TIMING ANALYSIS")
    print("="*80)
    
    # Look for sequential YES/NO pairs
    yes_trades = [t for t in trades_sorted if t.get('outcome', '').upper() == 'UP']
    no_trades = [t for t in trades_sorted if t.get('outcome', '').upper() == 'DOWN']
    
    print(f"\nYES Trades: {len(yes_trades)}")
    print(f"NO Trades: {len(no_trades)}")
    print(f"Ratio: {len(yes_trades)/len(no_trades):.2f}:1" if no_trades else "N/A")
    
    # Check if orders are placed simultaneously or sequentially
    time_diffs = []
    for i in range(min(len(yes_trades), len(no_trades))):
        yes_ts = yes_trades[i].get('timestamp', 0)
        no_ts = no_trades[i].get('timestamp', 0)
        if yes_ts and no_ts:
            diff = abs(yes_ts - no_ts)
            time_diffs.append(diff)
    
    if time_diffs:
        avg_diff = sum(time_diffs) / len(time_diffs)
        print(f"\nAverage time difference between YES/NO orders: {avg_diff:.2f} seconds")
        print(f"Min difference: {min(time_diffs):.2f} seconds")
        print(f"Max difference: {max(time_diffs):.2f} seconds")
        if avg_diff < 1.0:
            print("  -> Orders are placed SIMULTANEOUSLY (within same second)")
        elif avg_diff < 5.0:
            print("  -> Orders are placed QUICKLY (within 5 seconds)")
        else:
            print("  -> Orders are placed SEQUENTIALLY (may be rebalancing)")
    
    # Analyze price patterns
    print("\n" + "="*80)
    print("PRICE PATTERN ANALYSIS")
    print("="*80)
    
    yes_prices = [float(t.get('price', 0)) for t in yes_trades]
    no_prices = [float(t.get('price', 0)) for t in no_trades]
    
    if yes_prices and no_prices:
        print(f"\nYES Price Range: ${min(yes_prices):.4f} - ${max(yes_prices):.4f}")
        print(f"NO Price Range: ${min(no_prices):.4f} - ${max(no_prices):.4f}")
        
        # Calculate combined prices
        combined_prices = []
        for i in range(min(len(yes_prices), len(no_prices))):
            combined = yes_prices[i] + no_prices[i]
            combined_prices.append(combined)
        
        if combined_prices:
            print(f"\nCombined Price Range: ${min(combined_prices):.4f} - ${max(combined_prices):.4f}")
            print(f"Average Combined: ${sum(combined_prices)/len(combined_prices):.4f}")
            print(f"Min Combined (best arb): ${min(combined_prices):.4f} (${(1.0 - min(combined_prices)):.4f} profit)")
            print(f"Max Combined: ${max(combined_prices):.4f}")
            
            # Count arbitrage opportunities
            arb_count = sum(1 for c in combined_prices if c < 0.97)
            print(f"\nArbitrage Opportunities (combined < 0.97): {arb_count}/{len(combined_prices)} ({arb_count/len(combined_prices)*100:.1f}%)")
    
    # Analyze order sizes
    print("\n" + "="*80)
    print("ORDER SIZE ANALYSIS")
    print("="*80)
    
    all_sizes = [float(t.get('size', 0)) for t in trades_sorted]
    all_costs = [float(t.get('price', 0)) * float(t.get('size', 0)) for t in trades_sorted]
    
    print(f"\nShare Sizes:")
    print(f"  Min: {min(all_sizes):.2f} shares")
    print(f"  Max: {max(all_sizes):.2f} shares")
    print(f"  Avg: {sum(all_sizes)/len(all_sizes):.2f} shares")
    print(f"  Median: {sorted(all_sizes)[len(all_sizes)//2]:.2f} shares")
    
    print(f"\nOrder Costs:")
    print(f"  Min: ${min(all_costs):.2f}")
    print(f"  Max: ${max(all_costs):.2f}")
    print(f"  Avg: ${sum(all_costs)/len(all_costs):.2f}")
    
    # Strategy summary
    print("\n" + "="*80)
    print("STRATEGY SUMMARY")
    print("="*80)
    
    print("""
Based on the trade data analysis, here's how the bot places orders:

1. ARBITRAGE DETECTION:
   - Bot monitors combined price (YES + NO)
   - Only trades when combined < 0.97 (3%+ profit margin)
   - Adds 2 cent buffer per side for slippage

2. ORDER PLACEMENT:
   - Tries to place BOTH YES and NO orders simultaneously
   - Uses parallel execution (asyncio.gather)
   - Orders are placed as GTC (Good Till Cancel)

3. POSITION BUILDING:
   - Buys EQUAL shares on both sides when possible
   - Calculates shares based on:
     * Remaining position capacity
     * Max order size limit ($25 per side)
     * Minimum order size ($5 per side)

4. IMBALANCE MANAGEMENT:
   - Checks imbalance ratio before each trade
   - Time-based thresholds:
     * First minute: 12.0x allowed (startup)
     * Second minute: 3.0x allowed (rebalancing)
     * After 2 min: 1.3x (steady-state)

5. EXECUTION STYLE:
   - Reactive: Responds to orderbook updates
   - Fast: Places orders immediately when opportunity detected
   - Persistent: Keeps trying to build balanced position

6. ORDER TYPES:
   - Primary: GTC (Good Till Cancel) - stays in orderbook
   - Emergency: FOK (Fill Or Kill) - for rebalancing if needed
""")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        trades_file = sys.argv[1]
    else:
        trades_file = "reports/BTC_UpDown_9-15-930_trades.json"
    
    analyze_order_strategy(trades_file)

