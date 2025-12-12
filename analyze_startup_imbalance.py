#!/usr/bin/env python3
"""
Analyze imbalance at market start and initial trading pattern
"""

import json
import os
import datetime
import matplotlib.pyplot as plt
import numpy as np

def analyze_startup_pattern(trades_file, market_start_time):
    """Analyze trading pattern in first few minutes"""
    
    with open(trades_file, 'r', encoding='utf-8') as f:
        trades = json.load(f)
    
    if not trades:
        return None
    
    trades_sorted = sorted(trades, key=lambda x: x.get('timestamp', 0))
    
    # Track position over time
    yes_shares = 0
    no_shares = 0
    
    startup_data = []
    max_imbalance_ratio = 1.3
    
    for trade in trades_sorted:
        side = trade.get('outcome', '').lower()
        trade_side = trade.get('side', '').upper()
        size = float(trade.get('size', 0))
        timestamp = trade.get('timestamp', 0)
        
        if not timestamp:
            continue
        
        if trade_side == 'BUY':
            if side == 'up':
                yes_shares += size
            else:
                no_shares += size
        
        # Calculate time from market start
        seconds_from_start = timestamp - market_start_time
        minutes_from_start = seconds_from_start / 60.0
        
        # Calculate imbalance
        if yes_shares > 0 and no_shares > 0:
            imbalance_ratio = max(yes_shares / no_shares, no_shares / yes_shares)
        elif yes_shares > 0:
            imbalance_ratio = float('inf')
        elif no_shares > 0:
            imbalance_ratio = float('inf')
        else:
            imbalance_ratio = 1.0
        
        startup_data.append({
            'minutes_from_start': minutes_from_start,
            'yes_shares': yes_shares,
            'no_shares': no_shares,
            'imbalance_ratio': imbalance_ratio if imbalance_ratio != float('inf') else 100,
            'side': side,
            'trade_side': trade_side,
            'size': size,
            'timestamp': timestamp
        })
    
    return startup_data

def create_startup_analysis():
    """Create detailed startup analysis"""
    import sys
    
    if len(sys.argv) > 1:
        # Accept trades file and report name as arguments
        trades_file = sys.argv[1]
        report_name = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(trades_file).replace('_trades.json', '')
        
        # Try to infer time from report name
        time_match = None
        if '10-00-1015' in report_name:
            time_match = {'start': '10:00:00', 'display': '10:00-10:15'}
        elif '10-30-1045' in report_name:
            time_match = {'start': '10:30:00', 'display': '10:30-10:45'}
        elif '9-15-930' in report_name:
            time_match = {'start': '09:15:00', 'display': '9:15-9:30'}
        elif '9-30-945' in report_name:
            time_match = {'start': '09:30:00', 'display': '9:30-9:45'}
        
        if time_match:
            markets = [{
                'name': report_name,
                'file': trades_file,
                'start': time_match['start'],
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
                'display': '9:15-9:30'
            },
            {
                'name': 'BTC_UpDown_9-30-945',
                'file': 'reports/BTC_UpDown_9-30-945_trades.json',
                'start': '09:30:00',
                'display': '9:30-9:45'
            },
            {
                'name': 'BTC_UpDown_10-00-1015',
                'file': 'reports/BTC_UpDown_10-00-1015_trades.json',
                'start': '10:00:00',
                'display': '10:00-10:15'
            },
            {
                'name': 'BTC_UpDown_10-30-1045',
                'file': 'reports/BTC_UpDown_10-30-1045_trades.json',
                'start': '10:30:00',
                'display': '10:30-10:45'
            }
        ]
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Market Startup Imbalance Analysis', fontsize=16, fontweight='bold')
    
    for market_idx, market in enumerate(markets):
        if not os.path.exists(market['file']):
            continue
        
        # Parse start time
        start_parts = market['start'].split(':')
        start_dt = datetime.datetime(2025, 12, 12, int(start_parts[0]), int(start_parts[1]), int(start_parts[2]))
        start_ts = start_dt.timestamp()
        
        startup_data = analyze_startup_pattern(market['file'], start_ts)
        
        if not startup_data:
            continue
        
        # Focus on first 5 minutes
        first_5_min = [d for d in startup_data if d['minutes_from_start'] <= 5.0]
        
        minutes = [d['minutes_from_start'] for d in first_5_min]
        yes_shares = [d['yes_shares'] for d in first_5_min]
        no_shares = [d['no_shares'] for d in first_5_min]
        imbalance_ratios = [d['imbalance_ratio'] for d in first_5_min]
        
        # 1. Shares over time (first 5 minutes)
        ax1 = axes[market_idx, 0]
        ax1.plot(minutes, yes_shares, color='green', linewidth=2, label='YES Shares', marker='o', markersize=3)
        ax1.plot(minutes, no_shares, color='red', linewidth=2, label='NO Shares', marker='s', markersize=3)
        ax1.fill_between(minutes, yes_shares, alpha=0.3, color='green')
        ax1.fill_between(minutes, no_shares, alpha=0.3, color='red')
        ax1.set_xlabel('Minutes from Market Start', fontsize=10)
        ax1.set_ylabel('Shares', fontsize=10)
        ax1.set_title(f'{market["display"]} - Shares Over Time (First 5 Min)', fontsize=11, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Imbalance ratio (first 5 minutes)
        ax2 = axes[market_idx, 1]
        ax2.plot(minutes, imbalance_ratios, color='purple', linewidth=2, marker='o', markersize=3)
        ax2.axhline(y=1.3, color='red', linestyle='--', linewidth=2, label='Max Limit (1.3)', alpha=0.7)
        ax2.axhline(y=1.0, color='green', linestyle='--', linewidth=1, label='Perfect Balance', alpha=0.5)
        ax2.fill_between(minutes, 1.0, imbalance_ratios, 
                         where=[r > 1.0 for r in imbalance_ratios],
                         alpha=0.2, color='red')
        ax2.set_xlabel('Minutes from Market Start', fontsize=10)
        ax2.set_ylabel('Imbalance Ratio', fontsize=10)
        ax2.set_title(f'{market["display"]} - Imbalance Ratio (First 5 Min)', fontsize=11, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, min(max(imbalance_ratios) * 1.1, 15) if imbalance_ratios else 5)
    
    plt.tight_layout()
    plt.savefig('reports/startup_imbalance_analysis.png', dpi=200, bbox_inches='tight')
    print("Startup imbalance analysis saved as 'reports/startup_imbalance_analysis.png'")
    plt.close()
    
    # Detailed analysis
    print("\n" + "="*80)
    print("MARKET STARTUP IMBALANCE ANALYSIS")
    print("="*80)
    
    for market in markets:
        if not os.path.exists(market['file']):
            continue
        
        start_parts = market['start'].split(':')
        start_dt = datetime.datetime(2025, 12, 12, int(start_parts[0]), int(start_parts[1]), int(start_parts[2]))
        start_ts = start_dt.timestamp()
        
        startup_data = analyze_startup_pattern(market['file'], start_ts)
        
        if not startup_data:
            continue
        
        # Analyze first minute
        first_minute = [d for d in startup_data if d['minutes_from_start'] <= 1.0]
        first_30_sec = [d for d in startup_data if d['minutes_from_start'] <= 0.5]
        
        print(f"\n{market['display']} Market:")
        print("-" * 60)
        
        # First trade analysis
        if startup_data:
            first_trade = startup_data[0]
            print(f"First Trade:")
            print(f"  Time: {first_trade['minutes_from_start']:.3f} min from start ({first_trade['minutes_from_start']*60:.1f} seconds)")
            print(f"  Side: {first_trade['side'].upper()}")
            print(f"  Size: {first_trade['size']:.2f} shares")
        
        # First 30 seconds
        if first_30_sec:
            yes_trades_30s = [d for d in first_30_sec if d['side'] == 'up']
            no_trades_30s = [d for d in first_30_sec if d['side'] == 'down']
            
            print(f"\nFirst 30 Seconds:")
            print(f"  YES trades: {len(yes_trades_30s)}")
            print(f"  NO trades: {len(no_trades_30s)}")
            
            if first_30_sec:
                final_30s = first_30_sec[-1]
                print(f"  YES shares: {final_30s['yes_shares']:.2f}")
                print(f"  NO shares: {final_30s['no_shares']:.2f}")
                if final_30s['yes_shares'] > 0 and final_30s['no_shares'] > 0:
                    ratio = max(final_30s['yes_shares'] / final_30s['no_shares'],
                              final_30s['no_shares'] / final_30s['yes_shares'])
                    print(f"  Imbalance ratio: {ratio:.2f}")
                elif final_30s['yes_shares'] > 0:
                    print(f"  Imbalance: Only YES shares (infinite ratio)")
                elif final_30s['no_shares'] > 0:
                    print(f"  Imbalance: Only NO shares (infinite ratio)")
        
        # First minute
        if first_minute:
            yes_trades_1m = [d for d in first_minute if d['side'] == 'up']
            no_trades_1m = [d for d in first_minute if d['side'] == 'down']
            
            print(f"\nFirst Minute:")
            print(f"  Total trades: {len(first_minute)}")
            print(f"  YES trades: {len(yes_trades_1m)}")
            print(f"  NO trades: {len(no_trades_1m)}")
            
            final_1m = first_minute[-1]
            print(f"  Final YES shares: {final_1m['yes_shares']:.2f}")
            print(f"  Final NO shares: {final_1m['no_shares']:.2f}")
            if final_1m['yes_shares'] > 0 and final_1m['no_shares'] > 0:
                ratio = max(final_1m['yes_shares'] / final_1m['no_shares'],
                          final_1m['no_shares'] / final_1m['yes_shares'])
                print(f"  Imbalance ratio: {ratio:.2f}")
                if ratio > 1.3:
                    print(f"  [EXCEEDS LIMIT] Ratio {ratio:.2f} > 1.3")
                else:
                    print(f"  [WITHIN LIMIT] Ratio {ratio:.2f} <= 1.3")
        
        # Find when balance is achieved
        balanced_trades = [d for d in startup_data 
                          if d['yes_shares'] > 0 and d['no_shares'] > 0 
                          and max(d['yes_shares']/d['no_shares'], d['no_shares']/d['yes_shares']) <= 1.3]
        
        if balanced_trades:
            first_balanced = balanced_trades[0]
            print(f"\nBalance Achieved:")
            print(f"  Time: {first_balanced['minutes_from_start']:.3f} min from start")
            print(f"  Trade #: {startup_data.index(first_balanced) + 1}")
            print(f"  YES shares: {first_balanced['yes_shares']:.2f}")
            print(f"  NO shares: {first_balanced['no_shares']:.2f}")
        
        # Find max imbalance
        valid_imbalances = [d for d in startup_data 
                           if d['imbalance_ratio'] != 100 and d['imbalance_ratio'] != float('inf')]
        if valid_imbalances:
            max_imbalance = max(valid_imbalances, key=lambda x: x['imbalance_ratio'])
            print(f"\nMax Imbalance:")
            print(f"  Time: {max_imbalance['minutes_from_start']:.3f} min from start")
            print(f"  Ratio: {max_imbalance['imbalance_ratio']:.2f}")
            print(f"  YES shares: {max_imbalance['yes_shares']:.2f}")
            print(f"  NO shares: {max_imbalance['no_shares']:.2f}")
    
    print("\n" + "="*80)
    print("KEY INSIGHTS:")
    print("="*80)
    
    # Check if bot buys one side first
    all_first_trades = []
    for market in markets:
        if not os.path.exists(market['file']):
            continue
        start_parts = market['start'].split(':')
        start_dt = datetime.datetime(2025, 12, 12, int(start_parts[0]), int(start_parts[1]), int(start_parts[2]))
        start_ts = start_dt.timestamp()
        startup_data = analyze_startup_pattern(market['file'], start_ts)
        if startup_data:
            all_first_trades.append(startup_data[0]['side'])
    
    if all_first_trades:
        print(f"\nFirst Trade Pattern:")
        yes_first = sum(1 for s in all_first_trades if s == 'up')
        no_first = sum(1 for s in all_first_trades if s == 'down')
        print(f"  YES first: {yes_first} markets")
        print(f"  NO first: {no_first} markets")
        
        if yes_first > 0 or no_first > 0:
            print(f"\n[PATTERN DETECTED] Bot may buy one side first, then the other")
            print(f"  -> This explains initial imbalance spike")
            print(f"  -> Imbalance threshold may be too strict for startup")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    create_startup_analysis()

