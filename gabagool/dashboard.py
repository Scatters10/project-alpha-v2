#!/usr/bin/env python3
"""
Real-time Dashboard for Gabagool Bot
Shows live trades, positions, and statistics
Updates every 5 seconds
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False

import threading
import time

app = Flask(__name__)
if CORS_AVAILABLE:
    CORS(app)

DB_PATH = 'gabagool_ultra.db'
STATE_FILE = 'gabagool_state.json'

# HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Gabagool Bot Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-card .label {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }
        .positions-section {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .positions-section h2 {
            color: #667eea;
            margin-bottom: 15px;
        }
        .position-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
        }
        .position-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .position-header h3 {
            color: #333;
        }
        .position-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        .position-stat {
            background: white;
            padding: 10px;
            border-radius: 5px;
        }
        .position-stat label {
            font-size: 12px;
            color: #666;
            display: block;
            margin-bottom: 5px;
        }
        .position-stat .value {
            font-size: 18px;
            font-weight: bold;
            color: #667eea;
        }
        .trades-section {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .trades-section h2 {
            color: #667eea;
            margin-bottom: 15px;
        }
        .trades-table {
            width: 100%;
            border-collapse: collapse;
        }
        .trades-table th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        .trades-table td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        .trades-table tr:hover {
            background: #f8f9fa;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .badge-success {
            background: #28a745;
            color: white;
        }
        .badge-warning {
            background: #ffc107;
            color: #333;
        }
        .badge-danger {
            background: #dc3545;
            color: white;
        }
        .badge-info {
            background: #17a2b8;
            color: white;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .status-online {
            background: #28a745;
            animation: pulse 2s infinite;
        }
        .status-offline {
            background: #dc3545;
        }
        .price-live {
            color: #28a745;
        }
        .price-stale {
            color: #dc3545;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .last-update {
            text-align: right;
            color: #666;
            font-size: 12px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Gabagool Bot Dashboard</h1>
            <p>
                <span class="status-indicator {% if live_state.wss_connected %}status-online{% else %}status-offline{% endif %}"></span>
                <strong>WebSocket:</strong> <span id="wss-status">{% if live_state.wss_connected %}🟢 Connected{% else %}🔴 Disconnected{% endif %}</span> | 
                <strong>Messages:</strong> {{ live_state.wss_messages }} | 
                <strong>Mode:</strong> {% if live_state.simulation_mode %}🔬 Simulation{% else %}🚀 Production{% endif %} |
                <strong>Last Update:</strong> <span id="last-update">{{ last_update }}</span>
            </p>
        </div>

        <div class="positions-section">
            <h2>📊 Live Market Prices</h2>
            {% if live_state.active_markets %}
                {% for market_id, market in live_state.active_markets.items() %}
                <div class="position-card">
                    <div class="position-header">
                        <h3>{{ market.symbol }} - {{ market.slug.split('-')[-1] if market.slug else 'Current Contract' }}</h3>
                        <span class="badge {% if market.arbitrage_opportunity %}badge-success{% else %}badge-info{% endif %}">
                            {% if market.arbitrage_opportunity %}💰 ARB OPPORTUNITY{% else %}No Arb{% endif %}
                        </span>
                    </div>
                    <div class="position-stats">
                        <div class="position-stat">
                            <label>YES Price</label>
                            <div class="value {% if market.yes_price %}price-live{% else %}price-stale{% endif %}">
                                {% if market.yes_price %}${{ "%.4f"|format(market.yes_price) }}{% else %}No Data{% endif %}
                            </div>
                        </div>
                        <div class="position-stat">
                            <label>NO Price</label>
                            <div class="value {% if market.no_price %}price-live{% else %}price-stale{% endif %}">
                                {% if market.no_price %}${{ "%.4f"|format(market.no_price) }}{% else %}No Data{% endif %}
                            </div>
                        </div>
                        <div class="position-stat">
                            <label>Combined Price</label>
                            <div class="value {% if market.combined_price %}price-live{% else %}price-stale{% endif %}">
                                {% if market.combined_price %}{{ "%.4f"|format(market.combined_price) }}{% else %}N/A{% endif %}
                            </div>
                        </div>
                        <div class="position-stat">
                            <label>Arbitrage Margin</label>
                            <div class="value {% if market.arbitrage_opportunity %}price-live{% else %}price-stale{% endif %}">
                                {% if market.combined_price %}{{ "%.2f"|format((1.0 - market.combined_price) * 100) }}%{% else %}N/A{% endif %}
                            </div>
                        </div>
                        <div class="position-stat">
                            <label>Position Cost</label>
                            <div class="value">${{ "%.2f"|format(market.total_cost) }}</div>
                        </div>
                        <div class="position-stat">
                            <label>Guaranteed Profit</label>
                            <div class="value">${{ "%.2f"|format(market.guaranteed_profit) }}</div>
                        </div>
                    </div>
                    <div style="margin-top: 10px; font-size: 11px; color: #666;">
                        {% if market.has_data %}
                            ✅ Receiving live price updates
                        {% else %}
                            ⚠️ Waiting for price data...
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <p style="color: #666; padding: 20px; text-align: center;">
                    {% if not live_state.wss_connected %}
                        ⚠️ WebSocket not connected. Waiting for bot to connect...
                    {% else %}
                        ⚠️ No active markets found. Bot may be discovering markets...
                    {% endif %}
                </p>
            {% endif %}
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Trades</h3>
                <div class="value">{{ stats.total_trades }}</div>
                <div class="label">All time</div>
            </div>
            <div class="stat-card">
                <h3>Total Spent</h3>
                <div class="value">${{ "%.2f"|format(stats.total_spent) }}</div>
                <div class="label">Capital deployed</div>
            </div>
            <div class="stat-card">
                <h3>Guaranteed Profit</h3>
                <div class="value">${{ "%.2f"|format(stats.guaranteed_profit) }}</div>
                <div class="label">From arbitrage</div>
            </div>
            <div class="stat-card">
                <h3>Active Positions</h3>
                <div class="value">{{ stats.active_positions }}</div>
                <div class="label">Markets</div>
            </div>
            <div class="stat-card">
                <h3>Opportunities Found</h3>
                <div class="value">{{ stats.opportunities }}</div>
                <div class="label">Arbitrage chances</div>
            </div>
            <div class="stat-card">
                <h3>Fill Rate</h3>
                <div class="value">{{ "%.1f"|format(stats.fill_rate) }}%</div>
                <div class="label">Orders filled</div>
            </div>
        </div>

        <div class="positions-section">
            <h2>💼 Active Positions (From Trades)</h2>
            {% if positions %}
                {% for symbol, pos in positions.items() %}
                <div class="position-card">
                    <div class="position-header">
                        <h3>{{ symbol }}</h3>
                        <span class="badge badge-info">Active</span>
                    </div>
                    <div class="position-stats">
                        <div class="position-stat">
                            <label>YES Shares</label>
                            <div class="value">{{ "%.2f"|format(pos.yes_shares) }}</div>
                        </div>
                        <div class="position-stat">
                            <label>NO Shares</label>
                            <div class="value">{{ "%.2f"|format(pos.no_shares) }}</div>
                        </div>
                        <div class="position-stat">
                            <label>Total Cost</label>
                            <div class="value">${{ "%.2f"|format(pos.total_cost) }}</div>
                        </div>
                        <div class="position-stat">
                            <label>Combined Price</label>
                            <div class="value">{{ "%.4f"|format(pos.avg_combined_price) }}</div>
                        </div>
                        <div class="position-stat">
                            <label>Guaranteed Profit</label>
                            <div class="value">${{ "%.2f"|format(pos.guaranteed_profit) }}</div>
                        </div>
                        <div class="position-stat">
                            <label>Imbalance Ratio</label>
                            <div class="value">{{ "%.2f"|format(pos.imbalance_ratio) }}</div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <p>No active positions</p>
            {% endif %}
        </div>

        <div class="trades-section">
            <h2>📈 Recent Trades (Last 50)</h2>
            <table class="trades-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Price</th>
                        <th>Shares</th>
                        <th>Cost</th>
                        <th>Combined</th>
                        <th>Profit</th>
                        <th>Latency</th>
                    </tr>
                </thead>
                <tbody>
                    {% for trade in recent_trades %}
                    <tr>
                        <td>{{ trade.timestamp[:19] }}</td>
                        <td><strong>{{ trade.symbol }}</strong></td>
                        <td><span class="badge {% if trade.side == 'YES' %}badge-success{% else %}badge-warning{% endif %}">{{ trade.side }}</span></td>
                        <td>${{ "%.4f"|format(trade.price) }}</td>
                        <td>{{ "%.2f"|format(trade.shares) }}</td>
                        <td>${{ "%.2f"|format(trade.cost) }}</td>
                        <td>{{ "%.4f"|format(trade.combined_price) if trade.combined_price else 'N/A' }}</td>
                        <td><strong>${{ "%.2f"|format(trade.profit) if trade.profit else '0.00' }}</strong></td>
                        <td>{{ "%.0f"|format(trade.latency_ms) }}ms</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="last-update">
            Auto-refreshes every 5 seconds | Last updated: {{ last_update }}
        </div>
    </div>

    <script>
        // Update timestamp every second
        setInterval(() => {
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }, 1000);
    </script>
</body>
</html>
"""

def get_db_connection():
    """Get database connection"""
    if not os.path.exists(DB_PATH):
        return None
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def calculate_imbalance_ratio(yes_shares, no_shares):
    """Calculate imbalance ratio"""
    if yes_shares == 0 and no_shares == 0:
        return 1.0
    if yes_shares == 0:
        return float('inf')
    if no_shares == 0:
        return float('inf')
    return max(yes_shares / no_shares, no_shares / yes_shares)

def get_stats():
    """Get overall statistics"""
    conn = get_db_connection()
    if not conn:
        return {
            'total_trades': 0,
            'total_spent': 0,
            'guaranteed_profit': 0,
            'active_positions': 0,
            'opportunities': 0,
            'fill_rate': 0
        }
    
    cursor = conn.cursor()
    
    # Total trades
    cursor.execute('SELECT COUNT(*) FROM trades')
    total_trades = cursor.fetchone()[0]
    
    # Total spent
    cursor.execute('SELECT SUM(cost) FROM trades')
    total_spent = cursor.fetchone()[0] or 0
    
    # Latest profit (from most recent trade)
    cursor.execute('SELECT profit FROM trades ORDER BY timestamp DESC LIMIT 1')
    latest_profit_row = cursor.fetchone()
    latest_profit = latest_profit_row[0] if latest_profit_row else 0
    
    # Active positions (unique symbols with recent trades)
    cursor.execute('''
        SELECT DISTINCT symbol, 
               SUM(CASE WHEN side = "YES" THEN shares ELSE 0 END) as yes_shares,
               SUM(CASE WHEN side = "NO" THEN shares ELSE 0 END) as no_shares,
               SUM(cost) as total_cost,
               AVG(combined_price) as avg_combined,
               MAX(profit) as max_profit
        FROM trades
        WHERE timestamp > datetime('now', '-1 hour')
        GROUP BY symbol
        HAVING yes_shares > 0 OR no_shares > 0
    ''')
    positions_data = cursor.fetchall()
    active_positions = len(positions_data)
    
    # Calculate total guaranteed profit from positions
    total_guaranteed = 0
    for row in positions_data:
        yes_shares, no_shares = row[1], row[2]
        avg_combined = row[4] or 0
        if avg_combined > 0 and avg_combined < 1.0:
            min_shares = min(yes_shares, no_shares)
            total_guaranteed += min_shares * (1.0 - avg_combined)
    
    # Orders sent/filled (approximate from trades)
    fill_rate = 100.0 if total_trades > 0 else 0
    
    conn.close()
    
    return {
        'total_trades': total_trades,
        'total_spent': total_spent,
        'guaranteed_profit': total_guaranteed or latest_profit,
        'active_positions': active_positions,
        'opportunities': total_trades,  # Approximate
        'fill_rate': fill_rate
    }

def get_positions():
    """Get current positions by symbol"""
    conn = get_db_connection()
    if not conn:
        return {}
    
    cursor = conn.cursor()
    
    # Get positions from last hour
    cursor.execute('''
        SELECT symbol,
               SUM(CASE WHEN side = "YES" THEN shares ELSE 0 END) as yes_shares,
               SUM(CASE WHEN side = "NO" THEN shares ELSE 0 END) as no_shares,
               SUM(CASE WHEN side = "YES" THEN cost ELSE 0 END) as yes_cost,
               SUM(CASE WHEN side = "NO" THEN cost ELSE 0 END) as no_cost,
               AVG(combined_price) as avg_combined_price,
               MAX(profit) as guaranteed_profit
        FROM trades
        WHERE timestamp > datetime('now', '-1 hour')
        GROUP BY symbol
        HAVING yes_shares > 0 OR no_shares > 0
    ''')
    
    positions = {}
    for row in cursor.fetchall():
        symbol, yes_shares, no_shares, yes_cost, no_cost, avg_combined, profit = row
        positions[symbol] = {
            'yes_shares': yes_shares or 0,
            'no_shares': no_shares or 0,
            'yes_cost': yes_cost or 0,
            'no_cost': no_cost or 0,
            'total_cost': (yes_cost or 0) + (no_cost or 0),
            'avg_combined_price': avg_combined or 0,
            'guaranteed_profit': profit or 0,
            'imbalance_ratio': calculate_imbalance_ratio(yes_shares or 0, no_shares or 0)
        }
    
    conn.close()
    return positions

def get_recent_trades(limit=50):
    """Get recent trades"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, symbol, side, price, shares, cost, 
               combined_price, profit, latency_ms
        FROM trades
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    trades = []
    for row in cursor.fetchall():
        trades.append({
            'timestamp': row[0],
            'symbol': row[1],
            'side': row[2],
            'price': row[3],
            'shares': row[4],
            'cost': row[5],
            'combined_price': row[6],
            'profit': row[7],
            'latency_ms': row[8] or 0
        })
    
    conn.close()
    return trades

def get_live_state():
    """Get live state from bot (prices, connection status)"""
    if not os.path.exists(STATE_FILE):
        return {
            'wss_connected': False,
            'wss_messages': 0,
            'wss_reconnects': 0,
            'active_markets': {},
            'timestamp': None,
            'simulation_mode': True
        }
    
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        # Check if data is stale (older than 10 seconds)
        if state.get('timestamp'):
            try:
                state_time = datetime.fromisoformat(state['timestamp'].replace('Z', '+00:00'))
                age = (datetime.now(state_time.tzinfo) - state_time).total_seconds()
                if age > 10:
                    state['wss_connected'] = False  # Mark as disconnected if stale
            except:
                pass
        
        return state
    except Exception as e:
        return {
            'wss_connected': False,
            'wss_messages': 0,
            'wss_reconnects': 0,
            'active_markets': {},
            'timestamp': None,
            'error': str(e)
        }

@app.route('/')
def dashboard():
    """Main dashboard page"""
    stats = get_stats()
    positions = get_positions()
    recent_trades = get_recent_trades(50)
    live_state = get_live_state()
    last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template_string(
        DASHBOARD_HTML,
        stats=stats,
        positions=positions,
        recent_trades=recent_trades,
        live_state=live_state,
        last_update=last_update
    )

@app.route('/api/data')
def api_data():
    """API endpoint for JSON data"""
    return jsonify({
        'stats': get_stats(),
        'positions': get_positions(),
        'recent_trades': get_recent_trades(50),
        'live_state': get_live_state(),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Gabagool Dashboard Starting...")
    print("=" * 70)
    print(f"📊 Dashboard URL: http://localhost:5000")
    print(f"📡 API Endpoint: http://localhost:5000/api/data")
    print(f"💾 Database: {DB_PATH}")
    print("=" * 70)
    print("\n💡 Tip: Keep this running while the bot is active")
    print("   The dashboard auto-refreshes every 5 seconds\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

