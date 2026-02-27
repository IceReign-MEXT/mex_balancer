"""
📊 ADVANCED ANALYTICS
Deep insights into trading performance and market trends
"""

import json
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger

class AdvancedAnalytics:
    """Comprehensive trading analytics"""
    
    def __init__(self):
        self.trades_history = []
        self.market_data = defaultdict(list)
    
    def record_trade_analytics(self, trade_data: Dict):
        """Record detailed trade data"""
        self.trades_history.append({
            "timestamp": datetime.now().isoformat(),
            "token": trade_data.get("token"),
            "amount": trade_data.get("amount"),
            "profit": trade_data.get("profit"),
            "fee": trade_data.get("fee"),
            "tier": trade_data.get("tier"),
            "entry_price": trade_data.get("entry_price"),
            "exit_price": trade_data.get("exit_price"),
            "duration_seconds": trade_data.get("duration", 0)
        })
    
    def get_user_analytics(self, user_id: int) -> Dict:
        """Generate comprehensive user analytics"""
        user_trades = [t for t in self.trades_history if t.get("user_id") == user_id]
        
        if not user_trades:
            return {"error": "No trade history"}
        
        profits = [t['profit'] for t in user_trades]
        fees = [t['fee'] for t in user_trades]
        
        return {
            "total_trades": len(user_trades),
            "winning_trades": len([p for p in profits if p > 0]),
            "losing_trades": len([p for p in profits if p < 0]),
            "win_rate": len([p for p in profits if p > 0]) / len(profits) * 100,
            "avg_profit": sum(profits) / len(profits),
            "avg_fee": sum(fees) / len(fees),
            "best_trade": max(profits),
            "worst_trade": min(profits),
            "profit_factor": abs(sum([p for p in profits if p > 0]) / sum([p for p in profits if p < 0])) if sum([p for p in profits if p < 0]) != 0 else float('inf'),
            "sharpe_ratio": self.calculate_sharpe(profits),
            "avg_trade_duration": sum([t.get('duration_seconds', 0) for t in user_trades]) / len(user_trades)
        }
    
    def calculate_sharpe(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0.0
        
        avg_return = sum(returns) / len(returns)
        variance = sum([(r - avg_return) ** 2 for r in returns]) / len(returns)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0.0
        
        return avg_return / std_dev
    
    def get_market_insights(self) -> Dict:
        """Generate market-wide insights"""
        if not self.trades_history:
            return {"error": "No market data"}
        
        last_24h = datetime.now() - timedelta(hours=24)
        recent_trades = [t for t in self.trades_history if datetime.fromisoformat(t['timestamp']) > last_24h]
        
        token_performance = defaultdict(lambda: {"trades": 0, "profit": 0.0})
        for trade in recent_trades:
            token = trade['token']
            token_performance[token]['trades'] += 1
            token_performance[token]['profit'] += trade['profit']
        
        # Top performing tokens
        top_tokens = sorted(
            token_performance.items(),
            key=lambda x: x[1]['profit'],
            reverse=True
        )[:5]
        
        return {
            "24h_volume": len(recent_trades),
            "24h_profit": sum([t['profit'] for t in recent_trades]),
            "most_traded_tokens": [t[0] for t in top_tokens],
            "avg_trade_size": sum([t['amount'] for t in recent_trades]) / len(recent_trades) if recent_trades else 0,
            "market_sentiment": "bullish" if sum([t['profit'] for t in recent_trades]) > 0 else "bearish"
        }

