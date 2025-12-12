#!/usr/bin/env python3
"""
Analyze how the bot handles inventory imbalance
"""

import json
import os
from collections import defaultdict

def analyze_imbalance_handling(trades_file):
    """Analyze how inventory imbalance is handled"""
    
    with open(trades_file, 'r', encoding='utf-8') as f:
        trades = json.load(f)
    
    if not trades:
        return None
    
    trades_sorted = sorted(trades, key=lambda x: x.get('timestamp', 0))
    
    # Track position over time
    yes_shares = 0
    no_shares = 0
    yes_cost = 0
    no_cost = 0
    
    imbalance_history = []
    max_imbalance_ratio = 1.3  # From gabagool config
    
    for trade in trades_sorted:
        side = trade.get('outcome', '').lower()
        trade_side = trade.get('side', '').upper()
        size = float(trade.get('size', 0))
        price = float(trade.get('price', 0))
        cost = size * price
        
        if trade_side == 'BUY':
            if side == 'up':
                yes_shares += size
                yes_cost += cost
            else:
                no_shares += size
                no_cost += cost
        elif trade_side == 'SELL':
            if side == 'up':
                yes_shares -= size
                yes_cost -= cost
            else:
                no_shares -= size
                no_cost -= cost
        
        # Calculate imbalance
        if yes_shares > 0 and no_shares > 0:
            imbalance_ratio_yes = yes_shares / no_shares
            imbalance_ratio_no = no_shares / yes_shares
            max_imbalance = max(imbalance_ratio_yes, imbalance_ratio_no)
        elif yes_shares > 0:
            max_imbalance = float('inf')  # Only YES shares
        elif no_shares > 0:
            max_imbalance = float('inf')  # Only NO shares
        else:
            max_imbalance = 1.0  # Balanced (both zero)
        
        imbalance_history.append({
            'yes_shares': yes_shares,
            'no_shares': no_shares,
            'imbalance_ratio': max_imbalance,
            'exceeds_limit': max_imbalance > max_imbalance_ratio if max_imbalance != float('inf') else True
        })
    
    # Find max imbalance
    valid_imbalances = [h['imbalance_ratio'] for h in imbalance_history 
                       if h['imbalance_ratio'] != float('inf')]
    max_imbalance_seen = max(valid_imbalances) if valid_imbalances else 1.0
    
    # Count times imbalance exceeded limit
    times_exceeded = sum(1 for h in imbalance_history if h['exceeds_limit'])
    
    # Final position
    final_yes = yes_shares
    final_no = no_shares
    final_imbalance = final_yes / final_no if final_no > 0 else (final_no / final_yes if final_yes > 0 else 1.0)
    
    return {
        'total_trades': len(trades_sorted),
        'sell_trades': len([t for t in trades_sorted if t.get('side', '').upper() == 'SELL']),
        'buy_trades': len([t for t in trades_sorted if t.get('side', '').upper() == 'BUY']),
        'final_yes_shares': final_yes,
        'final_no_shares': final_no,
        'final_imbalance_ratio': final_imbalance,
        'max_imbalance_seen': max_imbalance_seen,
        'max_imbalance_limit': max_imbalance_ratio,
        'times_exceeded_limit': times_exceeded,
        'imbalance_history': imbalance_history
    }

def main():
    import sys
    
    if len(sys.argv) > 1:
        # Accept trades file and report name as arguments
        trades_file = sys.argv[1]
        report_name = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(trades_file).replace('_trades.json', '')
        markets = [trades_file]
    else:
        # Default: analyze all known markets
        markets = [
            'reports/BTC_UpDown_9-15-930_trades.json',
            'reports/BTC_UpDown_9-30-945_trades.json',
            'reports/BTC_UpDown_10-00-1015_trades.json',
            'reports/BTC_UpDown_10-30-1045_trades.json'
        ]
    
    print("="*80)
    print("INVENTORY IMBALANCE ANALYSIS")
    print("="*80)
    
    for market_file in markets:
        if not os.path.exists(market_file):
            continue
        
        market_name = os.path.basename(market_file).replace('_trades.json', '')
        result = analyze_imbalance_handling(market_file)
        
        if not result:
            continue
        
        print(f"\n{market_name}:")
        print("-" * 60)
        print(f"Total Trades: {result['total_trades']}")
        print(f"  BUY trades: {result['buy_trades']}")
        print(f"  SELL trades: {result['sell_trades']}")
        
        print(f"\nFinal Position:")
        print(f"  YES shares: {result['final_yes_shares']:.2f}")
        print(f"  NO shares:  {result['final_no_shares']:.2f}")
        print(f"  Imbalance ratio: {result['final_imbalance_ratio']:.4f}")
        print(f"  Max allowed: {result['max_imbalance_limit']:.2f}")
        
        if result['final_imbalance_ratio'] > result['max_imbalance_limit']:
            print(f"  [EXCEEDED] Final imbalance exceeds limit!")
        else:
            print(f"  [WITHIN LIMIT] Final imbalance within allowed range")
        
        print(f"\nImbalance During Trading:")
        print(f"  Max imbalance seen: {result['max_imbalance_seen']:.4f}")
        print(f"  Times exceeded limit: {result['times_exceeded_limit']}")
        
        if result['sell_trades'] > 0:
            print(f"\n[REBALANCING DETECTED] Bot used SELL trades to rebalance!")
        else:
            print(f"\n[NO REBALANCING] Bot did not sell - only accumulated")
    
    print("\n" + "="*80)
    print("KEY FINDINGS:")
    print("="*80)
    
    # Check if _can_buy logic is working
    all_within_limit = all(
        analyze_imbalance_handling(m)['final_imbalance_ratio'] <= 1.3 
        for m in markets if os.path.exists(m)
    )
    
    if all_within_limit:
        print("\n[PREVENTION STRATEGY] Bot prevents imbalance by:")
        print("  1. Only buying when imbalance ratio < 1.3")
        print("  2. Always trying to buy EQUAL shares on both sides")
        print("  3. If one side fills but other doesn't, uses emergency sell")
    else:
        print("\n[IMBALANCE OCCURRED] Bot allowed some imbalance:")
        print("  - May be due to partial fills")
        print("  - Emergency sells may not have triggered")
        print("  - Or _can_buy() logic not fully enforced")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

