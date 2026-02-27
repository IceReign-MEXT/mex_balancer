"""
🐋 COPY TRADING MODULE
Auto-copy top traders from leaderboard
"""

from typing import Dict, List
from datetime import datetime
from loguru import logger

class CopyTrading:
    """Copy trading for Whale tier users"""
    
    def __init__(self):
        self.leaderboard = {}
        self.copy_settings = {}  # user_id -> {target_trader, percentage}
    
    def get_top_traders(self, limit: int = 10) -> List[Dict]:
        """Get top performing traders"""
        sorted_traders = sorted(
            self.leaderboard.items(),
            key=lambda x: x[1]['total_profit'],
            reverse=True
        )
        
        return [
            {
                "rank": i+1,
                "user_id": uid,
                "profit": data['total_profit'],
                "win_rate": data['win_rate'],
                "trades": data['total_trades']
            }
            for i, (uid, data) in enumerate(sorted_traders[:limit])
        ]
    
    def set_copy_target(self, user_id: int, target_id: int, percentage: float = 100.0):
        """Set trader to copy"""
        self.copy_settings[user_id] = {
            "target": target_id,
            "percentage": percentage,
            "enabled": True,
            "started": datetime.now().isoformat()
        }
        logger.info(f"User {user_id} now copying {target_id} at {percentage}%")
    
    async def execute_copy_trade(self, user_id: int, target_trade: Dict):
        """Execute trade on behalf of copier"""
        if user_id not in self.copy_settings:
            return None
        
        settings = self.copy_settings[user_id]
        if not settings['enabled']:
            return None
        
        # Calculate copy amount
        copy_amount = target_trade['amount'] * (settings['percentage'] / 100)
        
        return {
            "copied": True,
            "original_trader": settings['target'],
            "amount": copy_amount,
            "token": target_trade['token']
        }

