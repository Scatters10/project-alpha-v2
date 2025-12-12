#!/usr/bin/env python3
"""
Visualize inventory imbalance over time and analyze trading cutoff timing
"""

import json
import os
import datetime
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from collections import defaultdict

def load_trades(filename):
    """Load trades from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_imbalance_and_timing(trades, market_start_time, market_end_time):
    """Analyze imbalance over time and when trading stops"""
    if not trades:
        return None
    
    trades_sorted = sorted(trades, key=lambda x: x.get('timestamp', 0))
    
    # Track position over time
    yes_shares = 0
    no_shares = 0
    yes_cost = 0
    no_cost = 0
    
    imbalance_data = []
    time_data = []
    
    max_imbalance_ratio = 1.3
    
    for trade in trades_sorted:
        side = trade.get('outcome', '').lower()
        trade_side = trade.get('side', '').upper()
        size = float(trade.get('size', 0))
        price = float(trade.get('price', 0))
        cost = size * price
        timestamp = trade.get('timestamp', 0)
        
        if not timestamp:
            continue
        
        if trade_side == 'BUY':
            if side == 'up':
                yes_shares += size
                yes_cost += cost
            else:
                no_shares += size
                no_cost += cost
        
        # Calculate imbalance
        if yes_shares > 0 and no_shares > 0:
            imbalance_ratio_yes = yes_shares / no_shares
            imbalance_ratio_no = no_shares / yes_shares
            max_imbalance = max(imbalance_ratio_yes, imbalance_ratio_no)
            which_side_high = 'YES' if imbalance_ratio_yes > imbalance_ratio_no else 'NO'
        elif yes_shares > 0:
            max_imbalance = float('inf')  # Only YES
            which_side_high = 'YES'
        elif no_shares > 0:
            max_imbalance = float('inf')  # Only NO
            which_side_high = 'NO'
        else:
            max_imbalance = 1.0
            which_side_high = 'BALANCED'
        
        imbalance_data.append({
            'timestamp': timestamp,
            'datetime': datetime.datetime.fromtimestamp(timestamp),
            'yes_shares': yes_shares,
            'no_shares': no_shares,
            'imbalance_ratio': max_imbalance if max_imbalance != float('inf') else 100,  # Cap for visualization
            'exceeds_limit': max_imbalance > max_imbalance_ratio if max_imbalance != float('inf') else True,
            'which_side_high': which_side_high,
            'minutes_from_start': (timestamp - market_start_time) / 60.0,
            'minutes_to_end': (market_end_time - timestamp) / 60.0
        })
        time_data.append(timestamp)
    
    # Find last trade
    last_trade_time = time_data[-1] if time_data else None
    time_to_end = (market_end_time - last_trade_time) / 60.0 if last_trade_time else None
    
    return {
        'imbalance_data': imbalance_data,
        'last_trade_time': last_trade_time,
        'time_to_end_minutes': time_to_end,
        'market_end_time': market_end_time,
        'total_trades': len(trades_sorted)
    }

def create_imbalance_visualization(results, market_name, output_file):
    """Create comprehensive imbalance visualization"""
    
    fig, axes = plt.subplots(3, 1, figsize=(16, 12))
    fig.suptitle(f'Inventory Imbalance Analysis: {market_name}', fontsize=16, fontweight='bold')
    
    imbalance_data = results['imbalance_data']
    market_end_time = results['market_end_time']
    
    # Extract data
    timestamps = [d['datetime'] for d in imbalance_data]
    yes_shares = [d['yes_shares'] for d in imbalance_data]
    no_shares = [d['no_shares'] for d in imbalance_data]
    imbalance_ratios = [d['imbalance_ratio'] for d in imbalance_data]
    minutes_from_start = [d['minutes_from_start'] for d in imbalance_data]
    minutes_to_end = [d['minutes_to_end'] for d in imbalance_data]
    
    # 1. Shares over time
    ax1 = axes[0]
    ax1.plot(timestamps, yes_shares, color='green', linewidth=2, label='YES Shares', marker='o', markersize=2)
    ax1.plot(timestamps, no_shares, color='red', linewidth=2, label='NO Shares', marker='s', markersize=2)
    ax1.fill_between(timestamps, yes_shares, alpha=0.3, color='green')
    ax1.fill_between(timestamps, no_shares, alpha=0.3, color='red')
    
    # Add market end line
    market_end_dt = datetime.datetime.fromtimestamp(market_end_time)
    ax1.axvline(x=market_end_dt, color='black', linestyle='--', linewidth=2, 
                label=f'Market End ({market_end_dt.strftime("%H:%M")})', alpha=0.7)
    
    # Add last trade marker
    if results['last_trade_time']:
        last_trade_dt = datetime.datetime.fromtimestamp(results['last_trade_time'])
        ax1.axvline(x=last_trade_dt, color='orange', linestyle=':', linewidth=2,
                   label=f'Last Trade ({last_trade_dt.strftime("%H:%M:%S")})', alpha=0.7)
    
    ax1.set_xlabel('Time', fontsize=11)
    ax1.set_ylabel('Shares', fontsize=11)
    ax1.set_title('YES vs NO Shares Over Time', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 2. Imbalance ratio over time
    ax2 = axes[1]
    ax2.plot(timestamps, imbalance_ratios, color='purple', linewidth=2, marker='o', markersize=2)
    ax2.axhline(y=1.3, color='red', linestyle='--', linewidth=2, 
               label='Max Imbalance Limit (1.3)', alpha=0.7)
    ax2.axhline(y=1.0, color='green', linestyle='--', linewidth=1, 
               label='Perfect Balance (1.0)', alpha=0.5)
    ax2.fill_between(timestamps, 1.0, imbalance_ratios, 
                     where=[r > 1.0 for r in imbalance_ratios],
                     alpha=0.2, color='red', label='Imbalance Zone')
    
    # Add market end line
    ax2.axvline(x=market_end_dt, color='black', linestyle='--', linewidth=2, alpha=0.7)
    
    # Add last trade marker
    if results['last_trade_time']:
        ax2.axvline(x=last_trade_dt, color='orange', linestyle=':', linewidth=2, alpha=0.7)
    
    ax2.set_xlabel('Time', fontsize=11)
    ax2.set_ylabel('Imbalance Ratio', fontsize=11)
    ax2.set_title('Imbalance Ratio Over Time (Ratio > 1.3 = Exceeds Limit)', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, min(max(imbalance_ratios) * 1.1, 5))  # Cap at 5 for readability
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 3. Time to market end (when trades occur)
    ax3 = axes[2]
    
    # Create histogram of trades by minutes to end
    bins = np.arange(0, 16, 0.5)  # 0 to 15 minutes in 30-second bins
    ax3.hist(minutes_to_end, bins=bins, color='steelblue', alpha=0.7, edgecolor='black')
    ax3.axvline(x=1.0, color='red', linestyle='--', linewidth=2, 
               label='1 Minute Before End (RISKY)', alpha=0.7)
    ax3.axvline(x=2.0, color='orange', linestyle='--', linewidth=2,
               label='2 Minutes Before End (CAUTION)', alpha=0.7)
    ax3.axvline(x=5.0, color='yellow', linestyle='--', linewidth=1,
               label='5 Minutes Before End (SAFE)', alpha=0.5)
    
    # Count trades in risky zone
    risky_trades = sum(1 for m in minutes_to_end if m < 1.0)
    caution_trades = sum(1 for m in minutes_to_end if 1.0 <= m < 2.0)
    safe_trades = sum(1 for m in minutes_to_end if m >= 2.0)
    
    ax3.set_xlabel('Minutes Before Market End', fontsize=11)
    ax3.set_ylabel('Number of Trades', fontsize=11)
    ax3.set_title('Trade Timing Relative to Market End (Risk Analysis)', fontsize=12, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.set_xlim(0, 15)
    
    # Add text annotation
    stats_text = (
        f"Last Trade: {results['time_to_end_minutes']:.2f} min before end\n"
        f"Risky Zone (<1 min): {risky_trades} trades ({risky_trades/len(minutes_to_end)*100:.1f}%)\n"
        f"Caution Zone (1-2 min): {caution_trades} trades ({caution_trades/len(minutes_to_end)*100:.1f}%)\n"
        f"Safe Zone (>2 min): {safe_trades} trades ({safe_trades/len(minutes_to_end)*100:.1f}%)"
    )
    ax3.text(0.98, 0.98, stats_text, transform=ax3.transAxes,
            fontsize=10, va='top', ha='right',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8, edgecolor='black'))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"Imbalance visualization saved as '{output_file}'")
    plt.close()

def analyze_all_markets():
    """Analyze all markets"""
    import sys
    
    if len(sys.argv) > 1:
        # Accept trades file, report name, and time range as arguments
        trades_file = sys.argv[1]
        report_name = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(trades_file).replace('_trades.json', '')
        
        # Try to infer time from report name
        # Format: BTC_UpDown_10-00-1015 -> 10:00-10:15
        time_match = None
        if '10-00-1015' in report_name:
            time_match = {'start': '10:00:00', 'end': '10:15:00', 'display': '10:00-10:15'}
        elif '10-30-1045' in report_name:
            time_match = {'start': '10:30:00', 'end': '10:45:00', 'display': '10:30-10:45'}
        elif '9-15-930' in report_name:
            time_match = {'start': '09:15:00', 'end': '09:30:00', 'display': '9:15-9:30'}
        elif '9-30-945' in report_name:
            time_match = {'start': '09:30:00', 'end': '09:45:00', 'display': '9:30-9:45'}
        
        if time_match:
            markets = [{
                'name': report_name,
                'file': trades_file,
                'start': time_match['start'],
                'end': time_match['end'],
                'display': time_match['display']
            }]
        else:
            print(f"Could not infer time range from report name: {report_name}")
            return
    else:
        # Default: analyze all known markets
        markets = [
            {
                'name': 'BTC_UpDown_9-15-930',
                'file': 'reports/BTC_UpDown_9-15-930_trades.json',
                'start': '09:15:00',
                'end': '09:30:00',
                'display': '9:15-9:30'
            },
            {
                'name': 'BTC_UpDown_9-30-945',
                'file': 'reports/BTC_UpDown_9-30-945_trades.json',
                'start': '09:30:00',
                'end': '09:45:00',
                'display': '9:30-9:45'
            },
            {
                'name': 'BTC_UpDown_10-00-1015',
                'file': 'reports/BTC_UpDown_10-00-1015_trades.json',
                'start': '10:00:00',
                'end': '10:15:00',
                'display': '10:00-10:15'
            },
            {
                'name': 'BTC_UpDown_10-30-1045',
                'file': 'reports/BTC_UpDown_10-30-1045_trades.json',
                'start': '10:30:00',
                'end': '10:45:00',
                'display': '10:30-10:45'
            }
        ]
    
    all_results = []
    
    for market in markets:
        if not os.path.exists(market['file']):
            continue
        
        trades = load_trades(market['file'])
        
        # Parse times
        start_parts = market['start'].split(':')
        end_parts = market['end'].split(':')
        start_dt = datetime.datetime(2025, 12, 12, int(start_parts[0]), int(start_parts[1]), int(start_parts[2]))
        end_dt = datetime.datetime(2025, 12, 12, int(end_parts[0]), int(end_parts[1]), int(end_parts[2]))
        
        start_ts = start_dt.timestamp()
        end_ts = end_dt.timestamp()
        
        results = analyze_imbalance_and_timing(trades, start_ts, end_ts)
        
        if results:
            results['market_name'] = market['display']
            results['market_file'] = market['file']
            all_results.append(results)
            
            # Create individual visualization
            output_file = f"reports/{market['name']}_imbalance_analysis.png"
            create_imbalance_visualization(results, market['display'], output_file)
    
    # Print summary
    print("\n" + "="*80)
    print("TRADING CUTOFF TIMING ANALYSIS")
    print("="*80)
    
    for result in all_results:
        print(f"\n{result['market_name']} Market:")
        print("-" * 60)
        
        if result['last_trade_time']:
            last_trade_dt = datetime.datetime.fromtimestamp(result['last_trade_time'])
            market_end_dt = datetime.datetime.fromtimestamp(result['market_end_time'])
            time_to_end = result['time_to_end_minutes']
            
            print(f"Market End: {market_end_dt.strftime('%H:%M:%S')}")
            print(f"Last Trade: {last_trade_dt.strftime('%H:%M:%S')}")
            print(f"Time to End: {time_to_end:.2f} minutes")
            
            # Risk assessment
            if time_to_end < 1.0:
                risk_level = "VERY RISKY"
                risk_color = "[RED]"
            elif time_to_end < 2.0:
                risk_level = "RISKY"
                risk_color = "[ORANGE]"
            elif time_to_end < 5.0:
                risk_level = "CAUTION"
                risk_color = "[YELLOW]"
            else:
                risk_level = "SAFE"
                risk_color = "[GREEN]"
            
            print(f"Risk Level: {risk_color} {risk_level}")
            
            # Count trades in risky zones
            imbalance_data = result['imbalance_data']
            minutes_to_end = [d['minutes_to_end'] for d in imbalance_data]
            risky = sum(1 for m in minutes_to_end if m < 1.0)
            caution = sum(1 for m in minutes_to_end if 1.0 <= m < 2.0)
            safe = sum(1 for m in minutes_to_end if m >= 2.0)
            
            print(f"\nTrade Distribution:")
            print(f"  < 1 min to end: {risky} trades ({risky/len(minutes_to_end)*100:.1f}%)")
            print(f"  1-2 min to end: {caution} trades ({caution/len(minutes_to_end)*100:.1f}%)")
            print(f"  > 2 min to end: {safe} trades ({safe/len(minutes_to_end)*100:.1f}%)")
            
            if risky > 0:
                print(f"\n[WARNING] Bot placed {risky} trades in the final minute!")
                print(f"  Risk: Orders may not fill before market resolution")
                print(f"  Risk: Partial fills could leave imbalanced position")
        else:
            print("No trades found")
    
    print("\n" + "="*80)
    print("KEY INSIGHTS:")
    print("="*80)
    
    # Overall pattern
    all_times_to_end = []
    for result in all_results:
        if result['time_to_end_minutes']:
            all_times_to_end.append(result['time_to_end_minutes'])
    
    if all_times_to_end:
        avg_time_to_end = np.mean(all_times_to_end)
        min_time_to_end = min(all_times_to_end)
        
        print(f"\nAverage time to end: {avg_time_to_end:.2f} minutes")
        print(f"Minimum time to end: {min_time_to_end:.2f} minutes")
        
        if min_time_to_end < 1.0:
            print("\n[CRITICAL] Bot trades VERY CLOSE to market end!")
            print("  -> High risk of unfilled orders")
            print("  -> Recommendation: Stop trading 2-3 minutes before end")
        elif min_time_to_end < 2.0:
            print("\n[WARNING] Bot trades close to market end")
            print("  -> Some risk of timing issues")
            print("  -> Recommendation: Consider stopping 1-2 minutes earlier")
        else:
            print("\n[SAFE] Bot stops trading with reasonable buffer")
            print("  -> Low risk of timing issues")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    analyze_all_markets()

