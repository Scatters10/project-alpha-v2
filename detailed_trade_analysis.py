#!/usr/bin/env python3
"""
Enhanced detailed trade analysis with visualizations
"""

import json
import datetime
from collections import defaultdict
from statistics import mean, median, stdev
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import sys

def load_trades(filename="trades.json"):
    """Load trades from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_trades_detailed(trades, report_name=None):
    """Perform detailed analysis with visualizations"""
    
    if not trades:
        print("No trades to analyze.")
        return
    
    # Set output file paths
    if report_name:
        import os
        os.makedirs("reports", exist_ok=True)
        output_file = os.path.join("reports", f"{report_name}_detailed_analysis.png")
    else:
        output_file = "detailed_trade_analysis.png"
    
    # Sort by timestamp
    trades_sorted = sorted(trades, key=lambda x: x.get('timestamp', 0))
    
    # Separate trades
    buy_up = [t for t in trades_sorted if t.get('side', '').upper() == 'BUY' and t.get('outcome', '').lower() == 'up']
    buy_down = [t for t in trades_sorted if t.get('side', '').upper() == 'BUY' and t.get('outcome', '').lower() == 'down']
    
    # Calculate cumulative positions
    yes_shares = []
    no_shares = []
    yes_cost = []
    no_cost = []
    combined_price = []
    timestamps = []
    cumulative_yes = 0
    cumulative_no = 0
    cumulative_yes_cost = 0
    cumulative_no_cost = 0
    
    for t in trades_sorted:
        ts = t.get('timestamp', 0)
        if ts:
            timestamps.append(datetime.datetime.fromtimestamp(ts))
            price = float(t.get('price', 0))
            size = float(t.get('size', 0))
            cost = price * size
            
            if t.get('outcome', '').lower() == 'up':
                cumulative_yes += size
                cumulative_yes_cost += cost
            else:
                cumulative_no += size
                cumulative_no_cost += cost
            
            yes_shares.append(cumulative_yes)
            no_shares.append(cumulative_no)
            yes_cost.append(cumulative_yes_cost)
            no_cost.append(cumulative_no_cost)
            
            # Get current prices for combined calculation
            if t.get('outcome', '').lower() == 'up':
                # Find latest down price
                latest_down_price = price
                for t2 in reversed(trades_sorted[:trades_sorted.index(t)+1]):
                    if t2.get('outcome', '').lower() == 'down':
                        latest_down_price = float(t2.get('price', 0))
                        break
                combined_price.append(price + latest_down_price)
            else:
                # Find latest up price
                latest_up_price = price
                for t2 in reversed(trades_sorted[:trades_sorted.index(t)+1]):
                    if t2.get('outcome', '').lower() == 'up':
                        latest_up_price = float(t2.get('price', 0))
                        break
                combined_price.append(latest_up_price + price)
    
    # Calculate arbitrage opportunities
    arb_opportunities = []
    for cp in combined_price:
        if cp < 1.0:
            arb_opportunities.append(1.0 - cp)
        else:
            arb_opportunities.append(0)
    
    # Create comprehensive visualization
    fig = plt.figure(figsize=(18, 14))
    gs = fig.add_gridspec(5, 2, hspace=0.4, wspace=0.3, height_ratios=[2, 1.5, 1.5, 1.5, 1])
    
    # 1. Price movement over time
    ax1 = fig.add_subplot(gs[0, :])
    
    up_prices = [float(t.get('price', 0)) for t in buy_up]
    up_times = [datetime.datetime.fromtimestamp(t.get('timestamp', 0)) for t in buy_up]
    down_prices = [float(t.get('price', 0)) for t in buy_down]
    down_times = [datetime.datetime.fromtimestamp(t.get('timestamp', 0)) for t in buy_down]
    
    ax1.scatter(up_times, up_prices, color='green', alpha=0.6, s=30, label='YES (Up) Price', marker='^')
    ax1.scatter(down_times, down_prices, color='red', alpha=0.6, s=30, label='NO (Down) Price', marker='v')
    
    # Add combined price line
    ax1_twin = ax1.twinx()
    ax1_twin.plot(timestamps, combined_price, color='blue', linewidth=2, alpha=0.7, label='Combined Price')
    ax1_twin.axhline(y=1.0, color='black', linestyle='--', linewidth=1, alpha=0.5, label='Parity ($1.00)')
    ax1_twin.fill_between(timestamps, combined_price, 1.0, where=[cp < 1.0 for cp in combined_price], 
                          color='green', alpha=0.2, label='Arbitrage Zone')
    ax1_twin.set_ylabel('Combined Price ($)', color='blue', fontsize=10)
    ax1_twin.tick_params(axis='y', labelcolor='blue')
    ax1_twin.set_ylim(0.85, 1.05)
    ax1_twin.legend(loc='upper right')
    
    ax1.set_xlabel('Time', fontsize=11)
    ax1.set_ylabel('Price ($)', fontsize=11)
    ax1.set_title('Price Movement Over Time', fontsize=13, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 1.0)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 2. Cumulative shares position
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(timestamps, yes_shares, color='green', linewidth=2, label='YES Shares', marker='o', markersize=3)
    ax2.plot(timestamps, no_shares, color='red', linewidth=2, label='NO Shares', marker='s', markersize=3)
    ax2.fill_between(timestamps, yes_shares, alpha=0.3, color='green')
    ax2.fill_between(timestamps, no_shares, alpha=0.3, color='red')
    ax2.set_xlabel('Time', fontsize=10)
    ax2.set_ylabel('Cumulative Shares', fontsize=10)
    ax2.set_title('Cumulative Position (Shares)', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 3. Cumulative cost
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(timestamps, yes_cost, color='green', linewidth=2, label='YES Cost', marker='o', markersize=3)
    ax3.plot(timestamps, no_cost, color='red', linewidth=2, label='NO Cost', marker='s', markersize=3)
    total_cost = [y + n for y, n in zip(yes_cost, no_cost)]
    ax3.plot(timestamps, total_cost, color='blue', linewidth=2.5, linestyle='--', label='Total Cost', alpha=0.8)
    ax3.fill_between(timestamps, yes_cost, alpha=0.3, color='green')
    ax3.fill_between(timestamps, no_cost, alpha=0.3, color='red')
    ax3.set_xlabel('Time', fontsize=10)
    ax3.set_ylabel('Cumulative Cost ($)', fontsize=10)
    ax3.set_title('Cumulative Cost Over Time', fontsize=12, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 4. Arbitrage opportunity over time
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.plot(timestamps, arb_opportunities, color='purple', linewidth=2, marker='o', markersize=2)
    ax4.fill_between(timestamps, arb_opportunities, alpha=0.4, color='purple')
    ax4.set_xlabel('Time', fontsize=10)
    ax4.set_ylabel('Arbitrage Opportunity ($)', fontsize=10)
    ax4.set_title('Arbitrage Opportunity Over Time', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Add text annotation for max arb opportunity
    if arb_opportunities:
        max_arb_idx = np.argmax(arb_opportunities)
        max_arb_val = arb_opportunities[max_arb_idx]
        if max_arb_val > 0:
            ax4.annotate(f'Max: ${max_arb_val:.4f}', 
                        xy=(timestamps[max_arb_idx], max_arb_val),
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    # 5. Trade size distribution
    ax5 = fig.add_subplot(gs[2, 1])
    all_sizes = [float(t.get('size', 0)) for t in trades_sorted]
    ax5.hist(all_sizes, bins=30, color='steelblue', alpha=0.7, edgecolor='black')
    ax5.axvline(mean(all_sizes), color='red', linestyle='--', linewidth=2, label=f'Mean: {mean(all_sizes):.2f}')
    ax5.axvline(median(all_sizes), color='green', linestyle='--', linewidth=2, label=f'Median: {median(all_sizes):.2f}')
    ax5.set_xlabel('Trade Size (Shares)', fontsize=10)
    ax5.set_ylabel('Frequency', fontsize=10)
    ax5.set_title('Trade Size Distribution', fontsize=12, fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3, axis='y')
    
    # 6. Price distribution
    ax6 = fig.add_subplot(gs[3, 0])
    ax6.hist(up_prices, bins=30, color='green', alpha=0.6, label='YES Prices', edgecolor='black')
    ax6.hist(down_prices, bins=30, color='red', alpha=0.6, label='NO Prices', edgecolor='black')
    ax6.set_xlabel('Price ($)', fontsize=10)
    ax6.set_ylabel('Frequency', fontsize=10)
    ax6.set_title('Price Distribution', fontsize=12, fontweight='bold')
    ax6.legend()
    ax6.grid(True, alpha=0.3, axis='y')
    
    # 7. Trading velocity (trades per minute)
    ax7 = fig.add_subplot(gs[3, 1])
    trades_by_minute = defaultdict(list)
    for t in trades_sorted:
        ts = t.get('timestamp', 0)
        if ts:
            dt = datetime.datetime.fromtimestamp(ts)
            minute_key = dt.replace(second=0, microsecond=0)
            trades_by_minute[minute_key].append(t)
    
    minutes = sorted(trades_by_minute.keys())
    trade_counts = [len(trades_by_minute[m]) for m in minutes]
    minute_labels = [m.strftime('%H:%M') for m in minutes]
    
    bars = ax7.bar(range(len(minutes)), trade_counts, color='orange', alpha=0.7, edgecolor='black')
    ax7.set_xlabel('Minute', fontsize=10)
    ax7.set_ylabel('Number of Trades', fontsize=10)
    ax7.set_title('Trading Velocity (Trades per Minute)', fontsize=12, fontweight='bold')
    ax7.set_xticks(range(len(minutes)))
    ax7.set_xticklabels(minute_labels, rotation=45, ha='right')
    ax7.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, (bar, count) in enumerate(zip(bars, trade_counts)):
        height = bar.get_height()
        ax7.text(bar.get_x() + bar.get_width()/2., height,
                f'{count}', ha='center', va='bottom', fontsize=8)
    
    # 8. Performance metrics summary
    ax8 = fig.add_subplot(gs[4, :])
    ax8.axis('off')
    
    # Calculate final metrics
    final_yes_shares = yes_shares[-1] if yes_shares else 0
    final_no_shares = no_shares[-1] if no_shares else 0
    final_total_cost = total_cost[-1] if total_cost else 0
    
    # Market resolved to NO (Down), so NO shares worth $1 each
    final_value = final_no_shares * 1.0  # NO shares are worth $1
    pnl = final_value - final_total_cost
    
    # Calculate average combined price
    avg_combined = mean(combined_price) if combined_price else 0
    min_combined = min(combined_price) if combined_price else 0
    max_arb = max(arb_opportunities) if arb_opportunities else 0
    
    summary_text = f"""
    PERFORMANCE SUMMARY
    {'='*80}
    Total Trades: {len(trades_sorted)} | Total Cost: ${final_total_cost:.2f} | Final Value: ${final_value:.2f}
    Net PnL: ${pnl:.2f} ({pnl/final_total_cost*100:.2f}%) | Final YES Shares: {final_yes_shares:.2f} | Final NO Shares: {final_no_shares:.2f}
    Average Combined Price: ${avg_combined:.4f} | Min Combined Price: ${min_combined:.4f} | Max Arbitrage Opportunity: ${max_arb:.4f}
    """
    
    ax8.text(0.5, 0.5, summary_text, transform=ax8.transAxes,
            fontsize=11, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=1', facecolor='lightblue', alpha=0.8),
            family='monospace')
    
    plt.suptitle(f'Trade Analysis: {trades[0].get("title", "Unknown Market")}', 
                fontsize=16, fontweight='bold', y=0.995)
    
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"Detailed analysis chart saved as '{output_file}'")
    plt.close()
    
    # Print detailed statistics
    print("\n" + "="*80)
    print("DETAILED STATISTICS")
    print("="*80)
    print(f"\nFinal Position:")
    print(f"  YES Shares: {final_yes_shares:.2f}")
    print(f"  NO Shares:  {final_no_shares:.2f}")
    print(f"  Total Cost: ${final_total_cost:.2f}")
    print(f"\nMarket Resolution: NO (Down)")
    print(f"  Final Value (NO shares @ $1.00): ${final_value:.2f}")
    print(f"  Net PnL: ${pnl:.2f} ({pnl/final_total_cost*100:.2f}%)")
    
    print(f"\nArbitrage Analysis:")
    print(f"  Average Combined Price: ${avg_combined:.4f}")
    print(f"  Minimum Combined Price: ${min_combined:.4f}")
    print(f"  Maximum Arbitrage Opportunity: ${max_arb:.4f} ({max_arb/min_combined*100:.2f}%)")
    print(f"  Trades with Arbitrage Opportunity: {sum(1 for a in arb_opportunities if a > 0)}/{len(arb_opportunities)}")
    
    print(f"\nTrading Patterns:")
    print(f"  Peak Trading Minute: {minute_labels[np.argmax(trade_counts)]} ({max(trade_counts)} trades)")
    print(f"  Average Trades per Minute: {mean(trade_counts):.1f}")
    print(f"  Total Trading Duration: {(timestamps[-1] - timestamps[0]).total_seconds()/60:.1f} minutes")
    
    print(f"\nPrice Statistics:")
    print(f"  YES Price Range: ${min(up_prices):.4f} - ${max(up_prices):.4f}")
    print(f"  NO Price Range:  ${min(down_prices):.4f} - ${max(down_prices):.4f}")
    print(f"  YES Avg Price: ${mean(up_prices):.4f}")
    print(f"  NO Avg Price:  ${mean(down_prices):.4f}")
    
    print("\n" + "="*80)

def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else "trades.json"
    report_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        trades = load_trades(filename)
        analyze_trades_detailed(trades, report_name)
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

