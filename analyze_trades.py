#!/usr/bin/env python3
"""
Comprehensive trade analysis script for Polymarket trades
"""

import json
import datetime
from collections import defaultdict
from statistics import mean, median, stdev
import sys

def load_trades(filename="trades.json"):
    """Load trades from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_trades(trades):
    """Perform comprehensive analysis on trades"""
    
    if not trades:
        print("No trades to analyze.")
        return
    
    # Sort by timestamp
    trades_sorted = sorted(trades, key=lambda x: x.get('timestamp', 0))
    
    # Basic statistics
    total_trades = len(trades)
    unique_timestamps = len(set(t.get('timestamp', 0) for t in trades))
    
    # Separate by side and outcome
    buy_trades = [t for t in trades if t.get('side', '').upper() == 'BUY']
    sell_trades = [t for t in trades if t.get('side', '').upper() == 'SELL']
    
    up_trades = [t for t in trades if t.get('outcome', '').lower() == 'up']
    down_trades = [t for t in trades if t.get('outcome', '').lower() == 'down']
    
    # Price analysis
    prices = [float(t.get('price', 0)) for t in trades]
    sizes = [float(t.get('size', 0)) for t in trades]
    costs = [p * s for p, s in zip(prices, sizes)]
    
    # Time analysis
    timestamps = [t.get('timestamp', 0) for t in trades_sorted]
    if timestamps:
        start_time = datetime.datetime.fromtimestamp(timestamps[0])
        end_time = datetime.datetime.fromtimestamp(timestamps[-1])
        duration = end_time - start_time
    else:
        start_time = end_time = duration = None
    
    # Group by outcome and side
    buy_up = [t for t in trades if t.get('side', '').upper() == 'BUY' and t.get('outcome', '').lower() == 'up']
    buy_down = [t for t in trades if t.get('side', '').upper() == 'BUY' and t.get('outcome', '').lower() == 'down']
    sell_up = [t for t in trades if t.get('side', '').upper() == 'SELL' and t.get('outcome', '').lower() == 'up']
    sell_down = [t for t in trades if t.get('side', '').upper() == 'SELL' and t.get('outcome', '').lower() == 'down']
    
    # Calculate totals by category
    def calc_totals(trade_list):
        total_shares = sum(float(t.get('size', 0)) for t in trade_list)
        total_cost = sum(float(t.get('price', 0)) * float(t.get('size', 0)) for t in trade_list)
        avg_price = total_cost / total_shares if total_shares > 0 else 0
        return total_shares, total_cost, avg_price, len(trade_list)
    
    buy_up_sh, buy_up_cost, buy_up_avg, buy_up_count = calc_totals(buy_up)
    buy_down_sh, buy_down_cost, buy_down_avg, buy_down_count = calc_totals(buy_down)
    sell_up_sh, sell_up_cost, sell_up_avg, sell_up_count = calc_totals(sell_up)
    sell_down_sh, sell_down_cost, sell_down_avg, sell_down_count = calc_totals(sell_down)
    
    # Net position
    net_up_shares = buy_up_sh - sell_up_sh
    net_down_shares = buy_down_sh - sell_down_sh
    net_exposure = (buy_up_cost + buy_down_cost) - (sell_up_cost + sell_down_cost)
    
    # Price distribution analysis
    up_prices = [float(t.get('price', 0)) for t in up_trades]
    down_prices = [float(t.get('price', 0)) for t in down_trades]
    
    # Time-based analysis
    trades_by_minute = defaultdict(list)
    for t in trades_sorted:
        ts = t.get('timestamp', 0)
        if ts:
            dt = datetime.datetime.fromtimestamp(ts)
            minute_key = dt.strftime('%H:%M')
            trades_by_minute[minute_key].append(t)
    
    # Print comprehensive report
    print("=" * 80)
    print("TRADE ANALYSIS REPORT")
    print("=" * 80)
    print(f"\nMarket: {trades[0].get('title', 'Unknown')}")
    print(f"Total Trades: {total_trades}")
    print(f"Unique Timestamps: {unique_timestamps}")
    
    if start_time and end_time:
        print(f"\nTime Range:")
        print(f"  Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  End:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Duration: {duration}")
    
    print(f"\n{'=' * 80}")
    print("TRADE BREAKDOWN BY TYPE")
    print(f"{'=' * 80}")
    print(f"\nBUY Trades:")
    print(f"  Total: {len(buy_trades)}")
    print(f"  Up (YES):   {buy_up_count:4d} trades | {buy_up_sh:8.2f} shares | ${buy_up_cost:10.2f} | Avg: ${buy_up_avg:.4f}")
    print(f"  Down (NO):  {buy_down_count:4d} trades | {buy_down_sh:8.2f} shares | ${buy_down_cost:10.2f} | Avg: ${buy_down_avg:.4f}")
    
    print(f"\nSELL Trades:")
    print(f"  Total: {len(sell_trades)}")
    print(f"  Up (YES):   {sell_up_count:4d} trades | {sell_up_sh:8.2f} shares | ${sell_up_cost:10.2f} | Avg: ${sell_up_avg:.4f}")
    print(f"  Down (NO):  {sell_down_count:4d} trades | {sell_down_sh:8.2f} shares | ${sell_down_cost:10.2f} | Avg: ${sell_down_avg:.4f}")
    
    print(f"\n{'=' * 80}")
    print("NET POSITION")
    print(f"{'=' * 80}")
    print(f"  Up (YES) shares:   {net_up_shares:8.2f}")
    print(f"  Down (NO) shares:  {net_down_shares:8.2f}")
    print(f"  Net exposure:      ${net_exposure:10.2f}")
    
    print(f"\n{'=' * 80}")
    print("PRICE STATISTICS")
    print(f"{'=' * 80}")
    if prices:
        print(f"\nAll Trades:")
        print(f"  Min:  ${min(prices):.4f}")
        print(f"  Max:  ${max(prices):.4f}")
        print(f"  Mean: ${mean(prices):.4f}")
        print(f"  Median: ${median(prices):.4f}")
        if len(prices) > 1:
            print(f"  Std Dev: ${stdev(prices):.4f}")
    
    if up_prices:
        print(f"\nUp (YES) Trades:")
        print(f"  Min:  ${min(up_prices):.4f}")
        print(f"  Max:  ${max(up_prices):.4f}")
        print(f"  Mean: ${mean(up_prices):.4f}")
        print(f"  Median: ${median(up_prices):.4f}")
        if len(up_prices) > 1:
            print(f"  Std Dev: ${stdev(up_prices):.4f}")
    
    if down_prices:
        print(f"\nDown (NO) Trades:")
        print(f"  Min:  ${min(down_prices):.4f}")
        print(f"  Max:  ${max(down_prices):.4f}")
        print(f"  Mean: ${mean(down_prices):.4f}")
        print(f"  Median: ${median(down_prices):.4f}")
        if len(down_prices) > 1:
            print(f"  Std Dev: ${stdev(down_prices):.4f}")
    
    print(f"\n{'=' * 80}")
    print("VOLUME STATISTICS")
    print(f"{'=' * 80}")
    if sizes:
        print(f"  Total Shares: {sum(sizes):.2f}")
        print(f"  Total Cost:   ${sum(costs):.2f}")
        print(f"  Avg Trade Size: {mean(sizes):.2f} shares")
        print(f"  Avg Trade Cost:  ${mean(costs):.2f}")
        print(f"  Min Trade Size:  {min(sizes):.2f} shares")
        print(f"  Max Trade Size:  {max(sizes):.2f} shares")
    
    print(f"\n{'=' * 80}")
    print("TRADING ACTIVITY BY MINUTE")
    print(f"{'=' * 80}")
    if trades_by_minute:
        sorted_minutes = sorted(trades_by_minute.items())
        print(f"\n{'Minute':<10} {'Trades':<10} {'Shares':<15} {'Cost ($)':<15}")
        print("-" * 50)
        for minute, minute_trades in sorted_minutes[:20]:  # Show first 20 minutes
            total_shares = sum(float(t.get('size', 0)) for t in minute_trades)
            total_cost = sum(float(t.get('price', 0)) * float(t.get('size', 0)) for t in minute_trades)
            print(f"{minute:<10} {len(minute_trades):<10} {total_shares:<15.2f} ${total_cost:<14.2f}")
        
        if len(sorted_minutes) > 20:
            print(f"\n... and {len(sorted_minutes) - 20} more minutes")
    
    # Price movement analysis
    print(f"\n{'=' * 80}")
    print("PRICE MOVEMENT ANALYSIS")
    print(f"{'=' * 80}")
    
    # Group trades by outcome and analyze price trends
    up_trades_sorted = sorted([t for t in trades_sorted if t.get('outcome', '').lower() == 'up'], 
                              key=lambda x: x.get('timestamp', 0))
    down_trades_sorted = sorted([t for t in trades_sorted if t.get('outcome', '').lower() == 'down'], 
                               key=lambda x: x.get('timestamp', 0))
    
    if up_trades_sorted:
        first_up_price = float(up_trades_sorted[0].get('price', 0))
        last_up_price = float(up_trades_sorted[-1].get('price', 0))
        up_change = last_up_price - first_up_price
        up_change_pct = (up_change / first_up_price * 100) if first_up_price > 0 else 0
        print(f"\nUp (YES) Price Movement:")
        print(f"  First: ${first_up_price:.4f}")
        print(f"  Last:  ${last_up_price:.4f}")
        print(f"  Change: ${up_change:.4f} ({up_change_pct:+.2f}%)")
    
    if down_trades_sorted:
        first_down_price = float(down_trades_sorted[0].get('price', 0))
        last_down_price = float(down_trades_sorted[-1].get('price', 0))
        down_change = last_down_price - first_down_price
        down_change_pct = (down_change / first_down_price * 100) if first_down_price > 0 else 0
        print(f"\nDown (NO) Price Movement:")
        print(f"  First: ${first_down_price:.4f}")
        print(f"  Last:  ${last_down_price:.4f}")
        print(f"  Change: ${down_change:.4f} ({down_change_pct:+.2f}%)")
    
    # Combined price analysis (arbitrage opportunity)
    if up_trades_sorted and down_trades_sorted:
        print(f"\nCombined Price Analysis:")
        first_combined = first_up_price + first_down_price
        last_combined = last_up_price + last_down_price
        combined_change = last_combined - first_combined
        print(f"  First Combined: ${first_combined:.4f}")
        print(f"  Last Combined:  ${last_combined:.4f}")
        print(f"  Change: ${combined_change:.4f}")
        if first_combined < 1.0:
            arb_opp_first = 1.0 - first_combined
            print(f"  Arbitrage Opportunity (first): ${arb_opp_first:.4f} ({arb_opp_first/first_combined*100:.2f}%)")
        if last_combined < 1.0:
            arb_opp_last = 1.0 - last_combined
            print(f"  Arbitrage Opportunity (last): ${arb_opp_last:.4f} ({arb_opp_last/last_combined*100:.2f}%)")
    
    print(f"\n{'=' * 80}")
    print("TRANSACTION ANALYSIS")
    print(f"{'=' * 80}")
    
    # Unique transaction hashes
    unique_txns = set(t.get('transactionHash', '') for t in trades if t.get('transactionHash'))
    print(f"\nUnique Transactions: {len(unique_txns)}")
    
    # Trades per transaction
    txn_counts = defaultdict(int)
    for t in trades:
        tx_hash = t.get('transactionHash', '')
        if tx_hash:
            txn_counts[tx_hash] += 1
    
    if txn_counts:
        avg_trades_per_txn = mean(txn_counts.values())
        max_trades_per_txn = max(txn_counts.values())
        print(f"  Avg trades per transaction: {avg_trades_per_txn:.2f}")
        print(f"  Max trades per transaction: {max_trades_per_txn}")
    
    print("\n" + "=" * 80)

def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else "trades.json"
    try:
        trades = load_trades(filename)
        analyze_trades(trades)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except json.JSONDecodeError:
        print(f"Error: File '{filename}' is not valid JSON.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

