#!/usr/bin/env python3
"""
Compare trading strategies across multiple markets
Analyze order placement timing and patterns
"""

import json
import os
import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates

def load_trades(filename):
    """Load trades from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_order_timing(trades, market_start_time):
    """Analyze when orders are placed relative to market start"""
    if not trades:
        return {}
    
    trades_sorted = sorted(trades, key=lambda x: x.get('timestamp', 0))
    
    # Get first trade timestamp (when bot started trading)
    first_trade_time = trades_sorted[0].get('timestamp', 0)
    if not first_trade_time:
        return {}
    
    first_trade_dt = datetime.datetime.fromtimestamp(first_trade_time)
    market_start_dt = datetime.datetime.fromtimestamp(market_start_time)
    
    # Calculate time from market start to first trade
    time_to_first_trade = (first_trade_time - market_start_time) / 60.0  # minutes
    
    # Analyze trade distribution over time
    time_buckets = defaultdict(int)  # seconds from market start
    price_at_time = []
    
    for trade in trades_sorted:
        ts = trade.get('timestamp', 0)
        if ts:
            seconds_from_start = ts - market_start_time
            minutes_from_start = seconds_from_start / 60.0
            
            # Bucket by minute
            bucket = int(minutes_from_start)
            time_buckets[bucket] += 1
            
            price = float(trade.get('price', 0))
            price_at_time.append({
                'minutes_from_start': minutes_from_start,
                'price': price,
                'side': trade.get('outcome', '').lower()
            })
    
    return {
        'time_to_first_trade_minutes': time_to_first_trade,
        'first_trade_time': first_trade_dt.strftime('%H:%M:%S'),
        'market_start_time': market_start_dt.strftime('%H:%M:%S'),
        'time_buckets': dict(time_buckets),
        'price_at_time': price_at_time,
        'total_trades': len(trades_sorted)
    }

def analyze_trading_pattern(trades):
    """Analyze trading pattern characteristics"""
    if not trades:
        return {}
    
    trades_sorted = sorted(trades, key=lambda x: x.get('timestamp', 0))
    
    # Separate by side
    yes_trades = [t for t in trades_sorted if t.get('outcome', '').lower() == 'up']
    no_trades = [t for t in trades_sorted if t.get('outcome', '').lower() == 'down']
    
    # Analyze trade sizes
    all_sizes = [float(t.get('size', 0)) for t in trades_sorted]
    
    # Analyze prices
    yes_prices = [float(t.get('price', 0)) for t in yes_trades]
    no_prices = [float(t.get('price', 0)) for t in no_trades]
    
    # Analyze timing patterns
    timestamps = [t.get('timestamp', 0) for t in trades_sorted if t.get('timestamp', 0)]
    if timestamps:
        start_time = datetime.datetime.fromtimestamp(timestamps[0])
        end_time = datetime.datetime.fromtimestamp(timestamps[-1])
        duration_minutes = (timestamps[-1] - timestamps[0]) / 60.0
    else:
        duration_minutes = 0
        start_time = end_time = None
    
    # Analyze simultaneous trades (same timestamp)
    timestamp_counts = defaultdict(int)
    for t in trades_sorted:
        ts = t.get('timestamp', 0)
        if ts:
            timestamp_counts[ts] += 1
    
    simultaneous_trades = sum(1 for count in timestamp_counts.values() if count > 1)
    max_simultaneous = max(timestamp_counts.values()) if timestamp_counts else 0
    
    # Analyze order distribution
    size_distribution = {
        'min': min(all_sizes) if all_sizes else 0,
        'max': max(all_sizes) if all_sizes else 0,
        'mean': np.mean(all_sizes) if all_sizes else 0,
        'median': np.median(all_sizes) if all_sizes else 0,
        'common_sizes': {}
    }
    
    # Count common sizes
    for size in all_sizes:
        rounded = round(size, 1)
        size_distribution['common_sizes'][rounded] = size_distribution['common_sizes'].get(rounded, 0) + 1
    
    return {
        'total_trades': len(trades_sorted),
        'yes_trades': len(yes_trades),
        'no_trades': len(no_trades),
        'duration_minutes': duration_minutes,
        'start_time': start_time.strftime('%H:%M:%S') if start_time else None,
        'end_time': end_time.strftime('%H:%M:%S') if end_time else None,
        'simultaneous_trades': simultaneous_trades,
        'max_simultaneous': max_simultaneous,
        'size_distribution': size_distribution,
        'yes_avg_price': np.mean(yes_prices) if yes_prices else 0,
        'no_avg_price': np.mean(no_prices) if no_prices else 0,
        'yes_price_range': (min(yes_prices), max(yes_prices)) if yes_prices else (0, 0),
        'no_price_range': (min(no_prices), max(no_prices)) if no_prices else (0, 0),
    }

def compare_markets():
    """Compare all markets in reports folder"""
    
    # Market data - we need to estimate market start times
    # 15-minute markets start at :00, :15, :30, :45
    markets = [
        {
            'name': 'BTC_UpDown_9-00-915',
            'file': 'reports/BTC_UpDown_9-00-915_trades.json',
            'market_start': '09:00:00',
            'display_name': '9:00-9:15'
        },
        {
            'name': 'BTC_UpDown_9-15-930',
            'file': 'reports/BTC_UpDown_9-15-930_trades.json',
            'market_start': '09:15:00',
            'display_name': '9:15-9:30'
        },
        {
            'name': 'BTC_UpDown_9-30-945',
            'file': 'reports/BTC_UpDown_9-30-945_trades.json',
            'market_start': '09:30:00',
            'display_name': '9:30-9:45'
        }
    ]
    
    results = []
    
    for market in markets:
        if not os.path.exists(market['file']):
            print(f"Warning: {market['file']} not found, skipping...")
            continue
        
        trades = load_trades(market['file'])
        
        # Parse market start time
        start_parts = market['market_start'].split(':')
        market_start_dt = datetime.datetime(2025, 12, 12, int(start_parts[0]), int(start_parts[1]), int(start_parts[2]))
        market_start_ts = market_start_dt.timestamp()
        
        timing_analysis = analyze_order_timing(trades, market_start_ts)
        pattern_analysis = analyze_trading_pattern(trades)
        
        results.append({
            'name': market['name'],
            'display_name': market['display_name'],
            'trades': trades,
            'timing': timing_analysis,
            'pattern': pattern_analysis
        })
    
    return results

def create_comparison_visualization(results):
    """Create comprehensive comparison visualization"""
    
    fig = plt.figure(figsize=(18, 14))
    gs = fig.add_gridspec(4, 2, hspace=0.4, wspace=0.3)
    
    # 1. Time to first trade
    ax1 = fig.add_subplot(gs[0, 0])
    market_names = [r['display_name'] for r in results]
    time_to_first = [r['timing'].get('time_to_first_trade_minutes', 0) for r in results]
    
    bars = ax1.bar(market_names, time_to_first, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    ax1.set_ylabel('Minutes from Market Start', fontsize=11)
    ax1.set_title('Time to First Trade (Order Placement Timing)', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    
    for i, (bar, time) in enumerate(zip(bars, time_to_first)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{time:.2f}m', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 2. Trade distribution over time (first 5 minutes)
    ax2 = fig.add_subplot(gs[0, 1])
    for i, result in enumerate(results):
        time_buckets = result['timing'].get('time_buckets', {})
        minutes = sorted([m for m in time_buckets.keys() if m <= 5])
        counts = [time_buckets.get(m, 0) for m in minutes]
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        ax2.plot(minutes, counts, marker='o', label=result['display_name'], 
                color=colors[i], linewidth=2, markersize=6)
    
    ax2.set_xlabel('Minutes from Market Start', fontsize=11)
    ax2.set_ylabel('Number of Trades', fontsize=11)
    ax2.set_title('Trading Activity in First 5 Minutes', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Simultaneous trades analysis
    ax3 = fig.add_subplot(gs[1, 0])
    simultaneous = [r['pattern'].get('simultaneous_trades', 0) for r in results]
    max_simultaneous = [r['pattern'].get('max_simultaneous', 0) for r in results]
    
    x = np.arange(len(market_names))
    width = 0.35
    ax3.bar(x - width/2, simultaneous, width, label='Timestamps with Multiple Trades', color='steelblue')
    ax3.bar(x + width/2, max_simultaneous, width, label='Max Simultaneous Trades', color='coral')
    ax3.set_ylabel('Count', fontsize=11)
    ax3.set_title('Simultaneous Trade Execution', fontsize=12, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(market_names)
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Trade size distribution
    ax4 = fig.add_subplot(gs[1, 1])
    for i, result in enumerate(results):
        sizes = [float(t.get('size', 0)) for t in result['trades']]
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        ax4.hist(sizes, bins=30, alpha=0.5, label=result['display_name'], 
                color=colors[i], edgecolor='black')
    
    ax4.set_xlabel('Trade Size (Shares)', fontsize=11)
    ax4.set_ylabel('Frequency', fontsize=11)
    ax4.set_title('Trade Size Distribution', fontsize=12, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    # 5. Price movement over time (first trade to last)
    ax5 = fig.add_subplot(gs[2, :])
    for i, result in enumerate(results):
        price_data = result['timing'].get('price_at_time', [])
        if price_data:
            yes_data = [p for p in price_data if p['side'] == 'up']
            no_data = [p for p in price_data if p['side'] == 'down']
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
            if yes_data:
                yes_times = [p['minutes_from_start'] for p in yes_data]
                yes_prices = [p['price'] for p in yes_data]
                ax5.scatter(yes_times, yes_prices, alpha=0.4, s=20, 
                          color=colors[i], marker='^', label=f"{result['display_name']} YES")
            if no_data:
                no_times = [p['minutes_from_start'] for p in no_data]
                no_prices = [p['price'] for p in no_data]
                ax5.scatter(no_times, no_prices, alpha=0.4, s=20,
                          color=colors[i], marker='v', label=f"{result['display_name']} NO")
    
    ax5.set_xlabel('Minutes from Market Start', fontsize=11)
    ax5.set_ylabel('Price ($)', fontsize=11)
    ax5.set_title('Price Movement Over Time (All Markets)', fontsize=12, fontweight='bold')
    ax5.legend(ncol=3, fontsize=8)
    ax5.grid(True, alpha=0.3)
    
    # 6. Trading duration and intensity
    ax6 = fig.add_subplot(gs[3, 0])
    durations = [r['pattern'].get('duration_minutes', 0) for r in results]
    total_trades = [r['pattern'].get('total_trades', 0) for r in results]
    trades_per_minute = [t/d if d > 0 else 0 for t, d in zip(total_trades, durations)]
    
    x = np.arange(len(market_names))
    ax6_twin = ax6.twinx()
    
    bars1 = ax6.bar(x - 0.2, durations, 0.4, label='Duration (min)', color='steelblue', alpha=0.7)
    bars2 = ax6_twin.bar(x + 0.2, trades_per_minute, 0.4, label='Trades/min', color='coral', alpha=0.7)
    
    ax6.set_ylabel('Duration (minutes)', fontsize=11, color='steelblue')
    ax6_twin.set_ylabel('Trades per Minute', fontsize=11, color='coral')
    ax6.set_title('Trading Duration vs Intensity', fontsize=12, fontweight='bold')
    ax6.set_xticks(x)
    ax6.set_xticklabels(market_names)
    ax6.tick_params(axis='y', labelcolor='steelblue')
    ax6_twin.tick_params(axis='y', labelcolor='coral')
    ax6.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}', ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        height = bar.get_height()
        ax6_twin.text(bar.get_x() + bar.get_width()/2., height,
                     f'{height:.1f}', ha='center', va='bottom', fontsize=9)
    
    # 7. Strategy comparison summary
    ax7 = fig.add_subplot(gs[3, 1])
    ax7.axis('off')
    
    summary_lines = []
    summary_lines.append("STRATEGY COMPARISON SUMMARY")
    summary_lines.append("=" * 60)
    
    for result in results:
        timing = result['timing']
        pattern = result['pattern']
        summary_lines.append(f"\n{result['display_name']}:")
        summary_lines.append(f"  First trade: {timing.get('time_to_first_trade_minutes', 0):.2f} min after market start")
        summary_lines.append(f"  Total trades: {pattern.get('total_trades', 0)}")
        summary_lines.append(f"  Duration: {pattern.get('duration_minutes', 0):.1f} min")
        summary_lines.append(f"  Trades/min: {pattern.get('total_trades', 0) / max(pattern.get('duration_minutes', 1), 1):.1f}")
        summary_lines.append(f"  Simultaneous trades: {pattern.get('simultaneous_trades', 0)}")
        summary_lines.append(f"  Max simultaneous: {pattern.get('max_simultaneous', 0)}")
        summary_lines.append(f"  Avg trade size: {pattern['size_distribution'].get('mean', 0):.2f} shares")
    
    summary_text = "\n".join(summary_lines)
    ax7.text(0.05, 0.95, summary_text, transform=ax7.transAxes,
            fontsize=9, va='top', ha='left', family='monospace',
            bbox=dict(boxstyle='round,pad=1', facecolor='lightblue', alpha=0.8))
    
    plt.suptitle('Trading Strategy Comparison Across Markets', fontsize=16, fontweight='bold', y=0.995)
    plt.savefig('reports/strategy_comparison.png', dpi=200, bbox_inches='tight')
    print("Strategy comparison saved as 'reports/strategy_comparison.png'")
    plt.close()

def print_detailed_analysis(results):
    """Print detailed analysis to console"""
    print("\n" + "="*80)
    print("DETAILED STRATEGY ANALYSIS")
    print("="*80)
    
    for result in results:
        print(f"\n{result['display_name']} Market:")
        print("-" * 60)
        
        timing = result['timing']
        pattern = result['pattern']
        
        print(f"\nOrder Placement Timing:")
        print(f"  Market started: {timing.get('market_start_time', 'N/A')}")
        print(f"  First trade: {timing.get('first_trade_time', 'N/A')}")
        print(f"  Time to first trade: {timing.get('time_to_first_trade_minutes', 0):.2f} minutes")
        
        if timing.get('time_to_first_trade_minutes', 0) < 0.5:
            print("  [IMMEDIATE] STRATEGY: Orders placed IMMEDIATELY at market start")
        elif timing.get('time_to_first_trade_minutes', 0) < 2:
            print("  [QUICK] STRATEGY: Orders placed VERY QUICKLY after market start")
        else:
            print("  [DELAYED] STRATEGY: Orders placed after market has been active")
        
        print(f"\nTrading Pattern:")
        print(f"  Total trades: {pattern.get('total_trades', 0)}")
        print(f"  YES trades: {pattern.get('yes_trades', 0)}")
        print(f"  NO trades: {pattern.get('no_trades', 0)}")
        print(f"  Trading duration: {pattern.get('duration_minutes', 0):.1f} minutes")
        print(f"  Trades per minute: {pattern.get('total_trades', 0) / max(pattern.get('duration_minutes', 1), 1):.1f}")
        
        print(f"\nExecution Style:")
        print(f"  Simultaneous trades: {pattern.get('simultaneous_trades', 0)}")
        print(f"  Max simultaneous: {pattern.get('max_simultaneous', 0)}")
        if pattern.get('max_simultaneous', 0) > 5:
            print("  [PARALLEL] STRATEGY: Heavy use of parallel order execution")
        else:
            print("  [SEQUENTIAL] STRATEGY: More sequential order execution")
        
        print(f"\nTrade Sizing:")
        size_dist = pattern.get('size_distribution', {})
        print(f"  Min size: {size_dist.get('min', 0):.2f} shares")
        print(f"  Max size: {size_dist.get('max', 0):.2f} shares")
        print(f"  Avg size: {size_dist.get('mean', 0):.2f} shares")
        print(f"  Median size: {size_dist.get('median', 0):.2f} shares")
        
        # Most common sizes
        common_sizes = sorted(size_dist.get('common_sizes', {}).items(), 
                            key=lambda x: x[1], reverse=True)[:3]
        if common_sizes:
            print(f"  Most common sizes: {', '.join([f'{s:.1f}sh ({c}x)' for s, c in common_sizes])}")
        
        print(f"\nPrice Characteristics:")
        print(f"  YES avg price: ${pattern.get('yes_avg_price', 0):.4f}")
        print(f"  NO avg price: ${pattern.get('no_avg_price', 0):.4f}")
        yes_range = pattern.get('yes_price_range', (0, 0))
        no_range = pattern.get('no_price_range', (0, 0))
        print(f"  YES price range: ${yes_range[0]:.4f} - ${yes_range[1]:.4f}")
        print(f"  NO price range: ${no_range[0]:.4f} - ${no_range[1]:.4f}")
    
    print("\n" + "="*80)
    print("KEY INSIGHTS:")
    print("="*80)
    
    # Compare timing
    timings = [r['timing'].get('time_to_first_trade_minutes', 0) for r in results]
    if all(t < 1 for t in timings):
        print("[IMMEDIATE] Orders are placed IMMEDIATELY when markets open")
        print("  -> Strategy: Bot is ready and waiting for market start")
    elif all(t < 2 for t in timings):
        print("[QUICK] Orders are placed VERY QUICKLY after market start")
        print("  -> Strategy: Bot reacts to market opening within seconds")
    else:
        print("[DELAYED] Orders are placed after some delay")
        print("  -> Strategy: Bot may wait for initial price discovery")
    
    # Compare simultaneous trades
    max_sims = [r['pattern'].get('max_simultaneous', 0) for r in results]
    if all(m > 5 for m in max_sims):
        print("\n[PARALLEL] Heavy use of parallel order execution")
        print("  -> Strategy: Bot places multiple orders simultaneously")
        print("  -> Likely using asyncio.gather() or similar parallel execution")
    else:
        print("\n[SEQUENTIAL] More sequential order execution")
        print("  -> Strategy: Bot places orders one at a time or in smaller batches")
    
    print("\n" + "="*80)

def main():
    results = compare_markets()
    
    if not results:
        print("No market data found. Make sure trade files exist in reports/ folder.")
        return
    
    create_comparison_visualization(results)
    print_detailed_analysis(results)

if __name__ == "__main__":
    main()

