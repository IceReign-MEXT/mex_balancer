"""
📊 ADVANCED ANALYTICS
Deep insights into trading performance
"""

from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict

class AdvancedAnalytics:
    """Comprehensive trading analytics"""
    
    def __init__(self):
        self.trades_history = []
    
    def record_trade_analytics(self, trade_data: Dict):
        """Record detailed trade data"""
        self.trades_history.append({
            "timestamp": datetime.now().isoformat(),
            "token": trade_data.get("token"),
            "amount": trade_data.get("amount"),
            "profit": trade_data.get("profit"),
            "fee": trade_data.get("fee"),
            "tier": trade_data.get("tier")
        })
    
    def get_user_analytics(self, user_id: int) -> Dict:
        """Generate comprehensive user analytics"""
        user_trades = [t for t in self.trades_history if t.get("user_id") == user_id]
        
        if not user_trades:
            return {"error": "No trade history"}
        
        profits = [t['profit'] for t in user_trades]
        
        return {
            "total_trades": len(user_trades),
            "winning_trades": len([p for p in profits if p > 0]),
            "win_rate": len([p for p in profits if p > 0]) / len(profits) * 100,
            "avg_profit": sum(profits) / len(profits),
            "best_trade": max(profits),
            "worst_trade": min(profits)
        }
