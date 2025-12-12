#!/usr/bin/env python3
"""
Arbitrage timing analysis - when were the best opportunities captured?
"""

import json
import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
import sys

def load_trades(filename="trades.json"):
    """Load trades from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_arbitrage_timing(trades, report_name=None):
    """Analyze when arbitrage opportunities were captured"""
    
    if not trades:
        print("No trades to analyze.")
        return
    
    # Set output file path
    if report_name:
        import os
        os.makedirs("reports", exist_ok=True)
        output_file = os.path.join("reports", f"{report_name}_arbitrage_timing.png")
    else:
        output_file = "arbitrage_timing_analysis.png"
    
    trades_sorted = sorted(trades, key=lambda x: x.get('timestamp', 0))
    
    # Track prices over time
    up_prices = {}
    down_prices = {}
    timestamps = []
    
    for t in trades_sorted:
        ts = t.get('timestamp', 0)
        if ts:
            dt = datetime.datetime.fromtimestamp(ts)
            timestamps.append(dt)
            price = float(t.get('price', 0))
            outcome = t.get('outcome', '').lower()
            
            if outcome == 'up':
                up_prices[ts] = price
            else:
                down_prices[ts] = price
    
    # Calculate combined prices and arbitrage opportunities for each trade
    trade_analysis = []
    current_up_price = None
    current_down_price = None
    
    for t in trades_sorted:
        ts = t.get('timestamp', 0)
        if not ts:
            continue
            
        price = float(t.get('price', 0))
        size = float(t.get('size', 0))
        outcome = t.get('outcome', '').lower()
        cost = price * size
        
        # Update current prices
        if outcome == 'up':
            current_up_price = price
        else:
            current_down_price = price
        
        # Calculate combined price if we have both
        combined_price = None
        arb_opportunity = None
        arb_percentage = None
        
        if current_up_price is not None and current_down_price is not None:
            combined_price = current_up_price + current_down_price
            if combined_price < 1.0:
                arb_opportunity = 1.0 - combined_price
                arb_percentage = (arb_opportunity / combined_price) * 100
        
        trade_analysis.append({
            'timestamp': datetime.datetime.fromtimestamp(ts),
            'outcome': outcome,
            'price': price,
            'size': size,
            'cost': cost,
            'combined_price': combined_price,
            'arb_opportunity': arb_opportunity,
            'arb_percentage': arb_percentage,
            'up_price': current_up_price,
            'down_price': current_down_price
        })
    
    # Filter trades with arbitrage opportunities
    arb_trades = [t for t in trade_analysis if t['arb_opportunity'] is not None and t['arb_opportunity'] > 0]
    
    # Group by time windows (every 30 seconds)
    time_windows = defaultdict(lambda: {'trades': [], 'total_cost': 0, 'total_shares': 0, 'avg_arb': 0, 'max_arb': 0})
    
    for t in arb_trades:
        # Round to nearest 30 seconds
        ts = t['timestamp']
        rounded_ts = ts.replace(second=(ts.second // 30) * 30, microsecond=0)
        time_windows[rounded_ts]['trades'].append(t)
        time_windows[rounded_ts]['total_cost'] += t['cost']
        time_windows[rounded_ts]['total_shares'] += t['size']
        time_windows[rounded_ts]['avg_arb'] = mean([tr['arb_opportunity'] for tr in time_windows[rounded_ts]['trades']])
        time_windows[rounded_ts]['max_arb'] = max([tr['arb_opportunity'] for tr in time_windows[rounded_ts]['trades']])
    
    # Create visualization
    fig, axes = plt.subplots(3, 1, figsize=(16, 12))
    fig.suptitle('Arbitrage Timing Analysis', fontsize=16, fontweight='bold')
    
    # 1. Arbitrage opportunity over time
    ax1 = axes[0]
    arb_times = [t['timestamp'] for t in arb_trades]
    arb_opps = [t['arb_opportunity'] for t in arb_trades]
    arb_percs = [t['arb_percentage'] for t in arb_trades]
    
    scatter = ax1.scatter(arb_times, arb_opps, c=arb_percs, cmap='RdYlGn', 
                         s=50, alpha=0.6, edgecolors='black', linewidth=0.5)
    ax1.set_xlabel('Time', fontsize=11)
    ax1.set_ylabel('Arbitrage Opportunity ($)', fontsize=11)
    ax1.set_title('Arbitrage Opportunities Captured Over Time', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label('Arbitrage %', fontsize=10)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax1.xaxis.set_major_locator(mdates.SecondLocator(interval=60))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Add annotation for best opportunities
    if arb_opps:
        top_5_indices = np.argsort(arb_opps)[-5:][::-1]
        for idx in top_5_indices[:3]:  # Annotate top 3
            ax1.annotate(f"${arb_opps[idx]:.4f}\n({arb_percs[idx]:.1f}%)",
                        xy=(arb_times[idx], arb_opps[idx]),
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                        fontsize=8, arrowprops=dict(arrowstyle='->', lw=1))
    
    # 2. Combined price over time
    ax2 = axes[1]
    combined_times = [t['timestamp'] for t in trade_analysis if t['combined_price'] is not None]
    combined_prices = [t['combined_price'] for t in trade_analysis if t['combined_price'] is not None]
    
    ax2.plot(combined_times, combined_prices, color='blue', linewidth=2, alpha=0.7, label='Combined Price')
    ax2.axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='Parity ($1.00)')
    ax2.fill_between(combined_times, combined_prices, 1.0, 
                     where=[cp < 1.0 for cp in combined_prices],
                     color='green', alpha=0.3, label='Arbitrage Zone')
    ax2.set_xlabel('Time', fontsize=11)
    ax2.set_ylabel('Combined Price ($)', fontsize=11)
    ax2.set_title('Combined Price (YES + NO) Over Time', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0.85, 1.05)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax2.xaxis.set_major_locator(mdates.SecondLocator(interval=60))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 3. Trading activity and arbitrage capture efficiency
    ax3 = axes[2]
    
    window_times = sorted(time_windows.keys())
    window_costs = [time_windows[t]['total_cost'] for t in window_times]
    window_avg_arb = [time_windows[t]['avg_arb'] * 1000 for t in window_times]  # Scale for visibility
    window_trade_counts = [len(time_windows[t]['trades']) for t in window_times]
    
    ax3_twin = ax3.twinx()
    
    bars = ax3.bar(range(len(window_times)), window_costs, alpha=0.6, color='steelblue', 
                   edgecolor='black', label='Cost per 30s Window')
    line = ax3_twin.plot(range(len(window_times)), window_avg_arb, color='red', 
                        linewidth=2, marker='o', markersize=4, label='Avg Arb Opp (×1000)')
    
    ax3.set_xlabel('Time Window (30s intervals)', fontsize=11)
    ax3.set_ylabel('Cost per Window ($)', fontsize=11, color='steelblue')
    ax3_twin.set_ylabel('Avg Arbitrage Opportunity (×1000)', fontsize=11, color='red')
    ax3.set_title('Trading Activity vs Arbitrage Opportunity by Time Window', 
                  fontsize=12, fontweight='bold')
    ax3.tick_params(axis='y', labelcolor='steelblue')
    ax3_twin.tick_params(axis='y', labelcolor='red')
    ax3.set_xticks(range(len(window_times)))
    ax3.set_xticklabels([t.strftime('%H:%M:%S') for t in window_times], 
                        rotation=45, ha='right', fontsize=8)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Add trade count labels
    for i, (bar, count) in enumerate(zip(bars, window_trade_counts)):
        if count > 0:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{count}', ha='center', va='bottom', fontsize=7, fontweight='bold')
    
    # Combine legends
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_twin.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"Arbitrage timing analysis saved as '{output_file}'")
    plt.close()
    
    # Print timing insights
    print("\n" + "="*80)
    print("ARBITRAGE TIMING INSIGHTS")
    print("="*80)
    
    if arb_trades:
        best_arb_trade = max(arb_trades, key=lambda x: x['arb_opportunity'])
        worst_arb_trade = min([t for t in arb_trades if t['arb_opportunity'] > 0], 
                              key=lambda x: x['arb_opportunity'])
        
        print(f"\nBest Arbitrage Opportunity Captured:")
        print(f"  Time: {best_arb_trade['timestamp'].strftime('%H:%M:%S')}")
        print(f"  Opportunity: ${best_arb_trade['arb_opportunity']:.4f} ({best_arb_trade['arb_percentage']:.2f}%)")
        print(f"  Combined Price: ${best_arb_trade['combined_price']:.4f}")
        print(f"  YES Price: ${best_arb_trade['up_price']:.4f} | NO Price: ${best_arb_trade['down_price']:.4f}")
        print(f"  Trade Size: {best_arb_trade['size']:.2f} shares | Cost: ${best_arb_trade['cost']:.2f}")
        
        print(f"\nWorst Arbitrage Opportunity (still profitable):")
        print(f"  Time: {worst_arb_trade['timestamp'].strftime('%H:%M:%S')}")
        print(f"  Opportunity: ${worst_arb_trade['arb_opportunity']:.4f} ({worst_arb_trade['arb_percentage']:.2f}%)")
        print(f"  Combined Price: ${worst_arb_trade['combined_price']:.4f}")
        
        # Time-based efficiency
        early_trades = [t for t in arb_trades if t['timestamp'] < arb_trades[len(arb_trades)//3]['timestamp']]
        mid_trades = [t for t in arb_trades if arb_trades[len(arb_trades)//3]['timestamp'] <= t['timestamp'] < arb_trades[2*len(arb_trades)//3]['timestamp']]
        late_trades = [t for t in arb_trades if t['timestamp'] >= arb_trades[2*len(arb_trades)//3]['timestamp']]
        
        print(f"\nTiming Efficiency Analysis:")
        print(f"  Early Period ({len(early_trades)} trades):")
        if early_trades:
            print(f"    Avg Arb Opp: ${mean([t['arb_opportunity'] for t in early_trades]):.4f}")
            print(f"    Total Cost: ${sum([t['cost'] for t in early_trades]):.2f}")
        print(f"  Mid Period ({len(mid_trades)} trades):")
        if mid_trades:
            print(f"    Avg Arb Opp: ${mean([t['arb_opportunity'] for t in mid_trades]):.4f}")
            print(f"    Total Cost: ${sum([t['cost'] for t in mid_trades]):.2f}")
        print(f"  Late Period ({len(late_trades)} trades):")
        if late_trades:
            print(f"    Avg Arb Opp: ${mean([t['arb_opportunity'] for t in late_trades]):.4f}")
            print(f"    Total Cost: ${sum([t['cost'] for t in late_trades]):.2f}")
        
        # Best time windows
        print(f"\nTop 5 Time Windows by Arbitrage Opportunity:")
        sorted_windows = sorted(time_windows.items(), key=lambda x: x[1]['avg_arb'], reverse=True)
        for i, (window_time, data) in enumerate(sorted_windows[:5], 1):
            print(f"  {i}. {window_time.strftime('%H:%M:%S')}: "
                  f"Avg Arb ${data['avg_arb']:.4f} | "
                  f"{len(data['trades'])} trades | "
                  f"${data['total_cost']:.2f} cost")
    
    print("\n" + "="*80)

def mean(lst):
    return sum(lst) / len(lst) if lst else 0

def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else "trades.json"
    report_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        trades = load_trades(filename)
        analyze_arbitrage_timing(trades, report_name)
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

