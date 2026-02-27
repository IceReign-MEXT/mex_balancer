"""Auto-trading logic with profit taking"""
import asyncio
from typing import Dict, List
from datetime import datetime
from loguru import logger

class AutoTrader:
    def __init__(self, sniper, db, fee_manager, channel_id: str):
        self.sniper = sniper
        self.db = db
        self.fee_manager = fee_manager
        self.channel_id = channel_id
        self.active_positions: Dict[int, Dict] = {}
        self.monitoring = False
    
    async def add_position(self, trade_id: int, token: str, entry_price: float, 
                          amount: float, user_id: int):
        """Add position to monitor"""
        self.active_positions[trade_id] = {
            'token': token,
            'entry_price': entry_price,
            'amount': amount,
            'user_id': user_id,
            'tp1_hit': False,
            'tp2_hit': False,
            'highest_pnl': 0
        }
        logger.info(f"Added position {trade_id} for monitoring")
    
    async def monitor_positions(self):
        """Background task to monitor all positions"""
        self.monitoring = True
        logger.info("🤖 Auto-trader monitoring started")
        
        while self.monitoring:
            try:
                for trade_id, position in list(self.active_positions.items()):
                    await self._check_position(trade_id, position)
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(5)
    
    async def _check_position(self, trade_id: int, position: Dict):
        """Check position and execute sells"""
        try:
            current_value = await self.sniper.get_token_value(
                position['token'], 
                position['amount']
            )
            invested_sol = position['entry_price'] * position['amount']
            
            if invested_sol == 0:
                return
            
            pnl_percent = ((current_value - invested_sol) / invested_sol) * 100
            position['highest_pnl'] = max(position['highest_pnl'], pnl_percent)
            
            # Stop Loss: -20%
            if pnl_percent <= -20:
                await self._execute_sell(
                    trade_id, position, current_value, pnl_percent, "STOP LOSS"
                )
                return
            
            # Take Profit 1: +100% (sell 50%)
            if pnl_percent >= 100 and not position['tp1_hit']:
                await self._execute_partial_sell(
                    trade_id, position, current_value, pnl_percent, "TP1", 0.5
                )
                position['tp1_hit'] = True
                return
            
            # Take Profit 2: +400% (sell remaining 50%)
            if pnl_percent >= 400 and not position['tp2_hit'] and position['tp1_hit']:
                await self._execute_sell(
                    trade_id, position, current_value, pnl_percent, "TP2"
                )
                position['tp2_hit'] = True
                return
            
            # Trailing stop: Drop 10% from peak after 3x
            if position['highest_pnl'] > 200:
                trailing_stop = position['highest_pnl'] - 10
                if pnl_percent < trailing_stop:
                    await self._execute_sell(
                        trade_id, position, current_value, pnl_percent, "TRAILING STOP"
                    )
                    return
            
            # Update DB with current P&L
            await self.db.update_trade_pnl(trade_id, pnl_percent)
            
        except Exception as e:
            logger.error(f"Position check error: {e}")
    
    async def _execute_sell(self, trade_id: int, position: Dict, 
                           current_value: float, pnl: float, reason: str):
        """Execute full sell"""
        try:
            # Execute swap back to SOL
            result = await self.sniper.sell_token(
                token_address=position['token'],
                amount=position['amount']
            )
            
            if result['success']:
                # Calculate fees on profit only
                profit_sol = max(0, current_value - (position['entry_price'] * position['amount']))
                fee = self.fee_manager.calculate_fee(profit_sol) if profit_sol > 0 else 0
                
                # Update database
                await self.db.update_trade_exit(
                    trade_id=trade_id,
                    exit_price=current_value / position['amount'],
                    pnl_percent=pnl,
                    status='closed'
                )
                
                # Remove from monitoring
                del self.active_positions[trade_id]
                
                # Notify user
                await self._notify_user(
                    position['user_id'],
                    f"🔴 *{reason} EXECUTED*\n"
                    f"Token: `{position['token']}`\n"
                    f"Exit P&L: {pnl:+.2f}%\n"
                    f"Fee: {fee:.4f} SOL\n"
                    f"TX: `{result['signature']}`"
                )
                
                logger.info(f"Sell executed for trade {trade_id}: {reason}")
                
        except Exception as e:
            logger.error(f"Sell execution failed: {e}")
    
    async def _execute_partial_sell(self, trade_id: int, position: Dict,
                                   current_value: float, pnl: float, reason: str, portion: float):
        """Execute partial sell (TP1)"""
        try:
            sell_amount = position['amount'] * portion
            
            result = await self.sniper.sell_token(
                token_address=position['token'],
                amount=sell_amount
            )
            
            if result['success']:
                position['amount'] -= sell_amount  # Reduce remaining amount
                
                await self._notify_user(
                    position['user_id'],
                    f"🟢 *{reason} EXECUTED (50%)*\n"
                    f"Token: `{position['token']}`\n"
                    f"Current P&L: {pnl:+.2f}%\n"
                    f"Remaining: 50% position\n"
                    f"Trailing stop activated"
                )
                
        except Exception as e:
            logger.error(f"Partial sell failed: {e}")
    
    async def _notify_user(self, user_id: int, message: str):
        """Send notification to user and channel"""
        try:
            from telegram import Bot
            from core.config import Config
            bot = Bot(token=Config().bot_token)
            
            # Send to user
            await bot.send_message(user_id, message, parse_mode="Markdown")
            
            # Send to channel
            await bot.send_message(
                self.channel_id,
                f"📊 *TRADE UPDATE*\n{message}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Notification failed: {e}")
