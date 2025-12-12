#!/usr/bin/env python3
"""
Query orderbook data directly from Polymarket CLOB API
Uses REST API endpoint: GET /book?token_id={token_id}
"""

import requests
import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

def get_orderbook(token_id: str):
    """
    Get orderbook for a specific token ID from Polymarket CLOB API
    
    Args:
        token_id: The CLOB token ID
    
    Returns:
        dict with bids and asks, or None if error
    """
    # Polymarket CLOB API endpoint
    url = f"https://clob.polymarket.com/book"
    params = {"token_id": token_id}
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API returned status {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"Error fetching orderbook: {e}")
        return None

def get_market_token_ids(slug: str):
    """Get token IDs for a market"""
    url = f"https://gamma-api.polymarket.com/markets/slug/{slug}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            clob_ids = data.get("clobTokenIds") or data.get("clob_token_ids")
            
            if isinstance(clob_ids, str):
                try:
                    clob_ids = json.loads(clob_ids)
                except:
                    clob_ids = [x.strip().strip('"') for x in clob_ids.strip("[]").split(",")]
            
            return clob_ids if isinstance(clob_ids, list) and len(clob_ids) >= 2 else None
    except Exception as e:
        print(f"Error fetching market: {e}")
    return None

def format_orderbook(book_data, token_name=""):
    """Format orderbook data for display"""
    if not book_data:
        return None
    
    # Handle different response formats
    bids = book_data.get('bids', book_data.get('buy', []))
    asks = book_data.get('asks', book_data.get('sell', []))
    
    best_bid = bids[0] if bids else None
    best_ask = asks[0] if asks else None
    
    result = {
        'bids': bids,
        'asks': asks,
        'best_bid': best_bid,
        'best_ask': best_ask,
        'best_bid_price': float(best_bid.get('price', 0)) if best_bid else None,
        'best_ask_price': float(best_ask.get('price', 0)) if best_ask else None,
    }
    
    if best_bid and best_ask:
        result['spread'] = result['best_ask_price'] - result['best_bid_price']
        result['mid_price'] = (result['best_bid_price'] + result['best_ask_price']) / 2
    
    return result

def main():
    print("="*70)
    print("POLYMARKET ORDERBOOK QUERY")
    print("="*70)
    
    if len(sys.argv) > 1:
        # Query specific token ID
        token_id = sys.argv[1]
        print(f"\nQuerying orderbook for token: {token_id}")
        book = get_orderbook(token_id)
        
        if book:
            formatted = format_orderbook(book)
            print("\n" + "="*70)
            print("ORDERBOOK DATA")
            print("="*70)
            if formatted['best_bid']:
                print(f"\nBest Bid: ${formatted['best_bid_price']:.4f} | Size: {formatted['best_bid'].get('size', 'N/A')}")
            if formatted['best_ask']:
                print(f"Best Ask: ${formatted['best_ask_price']:.4f} | Size: {formatted['best_ask'].get('size', 'N/A')}")
            if formatted.get('spread'):
                print(f"Spread: ${formatted['spread']:.4f}")
                print(f"Mid Price: ${formatted['mid_price']:.4f}")
            
            print(f"\nTop 5 Bids:")
            for i, bid in enumerate(formatted['bids'][:5]):
                price = float(bid.get('price', 0))
                size = float(bid.get('size', 0))
                print(f"  {i+1}. ${price:.4f} | Size: {size}")
            
            print(f"\nTop 5 Asks:")
            for i, ask in enumerate(formatted['asks'][:5]):
                price = float(ask.get('price', 0))
                size = float(ask.get('size', 0))
                print(f"  {i+1}. ${price:.4f} | Size: {size}")
        else:
            print("❌ Could not fetch orderbook")
    else:
        # Query current BTC market
        print("\nQuerying current BTC 15-minute market...")
        
        now = datetime.now(tz=ZoneInfo("America/New_York"))
        slot = (now.minute // 15) * 15
        ts = int(now.replace(minute=slot, second=0, microsecond=0)
                 .astimezone(ZoneInfo("UTC")).timestamp())
        slug = f"btc-updown-15m-{ts}"
        
        print(f"Market slug: {slug}")
        token_ids = get_market_token_ids(slug)
        
        if token_ids and len(token_ids) >= 2:
            yes_token = token_ids[0]
            no_token = token_ids[1]
            
            print(f"\nYES Token ID: {yes_token}")
            print(f"NO Token ID: {no_token}")
            
            print("\n" + "="*70)
            print("YES TOKEN ORDERBOOK (Buying YES shares)")
            print("="*70)
            yes_book = get_orderbook(yes_token)
            if yes_book:
                formatted = format_orderbook(yes_book, "YES")
                if formatted['best_ask']:
                    print(f"Best Ask (to buy): ${formatted['best_ask_price']:.4f} | Size: {formatted['best_ask'].get('size', 'N/A')}")
                if formatted['best_bid']:
                    print(f"Best Bid (to sell): ${formatted['best_bid_price']:.4f} | Size: {formatted['best_bid'].get('size', 'N/A')}")
                if formatted.get('spread'):
                    print(f"Spread: ${formatted['spread']:.4f}")
            else:
                print("❌ Could not fetch orderbook - market may not have liquidity yet")
            
            print("\n" + "="*70)
            print("NO TOKEN ORDERBOOK (Buying NO shares)")
            print("="*70)
            no_book = get_orderbook(no_token)
            if no_book:
                formatted = format_orderbook(no_book, "NO")
                if formatted['best_ask']:
                    print(f"Best Ask (to buy): ${formatted['best_ask_price']:.4f} | Size: {formatted['best_ask'].get('size', 'N/A')}")
                if formatted['best_bid']:
                    print(f"Best Bid (to sell): ${formatted['best_bid_price']:.4f} | Size: {formatted['best_bid'].get('size', 'N/A')}")
                if formatted.get('spread'):
                    print(f"Spread: ${formatted['spread']:.4f}")
            else:
                print("❌ Could not fetch orderbook - market may not have liquidity yet")
            
            # Calculate combined price
            if yes_book and no_book:
                yes_formatted = format_orderbook(yes_book)
                no_formatted = format_orderbook(no_book)
                if yes_formatted['best_ask_price'] and no_formatted['best_ask_price']:
                    combined = yes_formatted['best_ask_price'] + no_formatted['best_ask_price']
                    print("\n" + "="*70)
                    print("ARBITRAGE ANALYSIS")
                    print("="*70)
                    print(f"Combined Price (YES + NO): ${combined:.4f}")
                    arb_status = "YES" if combined < 1.0 else "NO"
                    profit = 1.0 - combined if combined < 1.0 else 0
                    print(f"Arbitrage Opportunity: {arb_status} (${profit:.4f} profit per share)")
        else:
            print("❌ Could not get token IDs for market")

if __name__ == "__main__":
    main()

