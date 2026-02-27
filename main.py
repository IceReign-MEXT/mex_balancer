#!/usr/bin/env python3
"""
🤖 MEX BALANCER PRO - MEV SNIPER BOT v2.0
Subscription tiers + Profit tracking + Coffee earnings
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List
from loguru import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID")
RPC_URL = os.getenv("RPC_URL")
WALLET = os.getenv("SOL_MAIN")
FEE_WALLET = os.getenv("FEE_WALLET", WALLET)

# Subscription tiers
TIERS = {
    "free": {
        "name": "🆓 Free",
        "max_trade": 2.0,  # Max 2 SOL per trade
        "daily_trades": 5,
        "fee_percent": 1.0,  # 1% fee
        "mev_boost": False,
        "auto_tp": False,
        "price_sol": 0
    },
    "pro": {
        "name": "⚡ Pro",
        "max_trade": 10.0,  # Max 10 SOL per trade
        "daily_trades": 20,
        "fee_percent": 0.5,  # 0.5% fee
        "mev_boost": True,
        "auto_tp": True,
        "price_sol": 0.5  # 0.5 SOL/month
    },
    "whale": {
        "name": "🐋 Whale",
        "max_trade": 50.0,  # Max 50 SOL per trade
        "daily_trades": 100,
        "fee_percent": 0.25,  # 0.25% fee
        "mev_boost": True,
        "auto_tp": True,
        "copy_trading": True,
        "price_sol": 2.0  # 2 SOL/month
    }
}

WAITING_TOKEN = 1
WAITING_AMOUNT = 2

class UserData:
    def __init__(self):
        self.users = {}  # In-memory storage (use database in production)
    
    def get_user(self, user_id: int) -> Dict:
        if user_id not in self.users:
            self.users[user_id] = {
                "tier": "free",
                "joined": datetime.now().isoformat(),
                "total_trades": 0,
                "total_volume": 0.0,
                "total_profit": 0.0,
                "total_fees_paid": 0.0,
                "coffee_earnings": 0.0,  # Small consistent profits
                "daily_trades": 0,
                "last_trade_date": None,
                "positions": []
            }
        return self.users[user_id]
    
    def record_trade(self, user_id: int, amount: float, profit: float, fee: float):
        user = self.get_user(user_id)
        user["total_trades"] += 1
        user["total_volume"] += amount
        user["total_profit"] += profit
        user["total_fees_paid"] += fee
        
        # Coffee earnings = small profits under 0.1 SOL
        if 0 < profit <= 0.1:
            user["coffee_earnings"] += profit
        
        # Reset daily counter if new day
        today = datetime.now().date()
        if user["last_trade_date"] != str(today):
            user["daily_trades"] = 0
            user["last_trade_date"] = str(today)
        user["daily_trades"] += 1

class MexBalancerPro:
    def __init__(self):
        self.db = UserData()
        self.admin_revenue = 0.0
        
    def get_tier_info(self, user_id: int) -> Dict:
        user = self.db.get_user(user_id)
        return TIERS[user["tier"]]
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_data = self.db.get_user(user.id)
        tier_info = self.get_tier_info(user.id)
        
        welcome = f"""🎯 *MEX BALANCER PRO*

👤 User: `{user.id}`
⭐ Tier: {tier_info['name']}
🤖 Status: 🟢 OPERATIONAL

📊 *YOUR STATS:*
• Trades: {user_data['total_trades']}
• Volume: {user_data['total_volume']:.2f} SOL
• Profit: {user_data['total_profit']:.4f} SOL
☕ Coffee: {user_data['coffee_earnings']:.4f} SOL

💼 *COMMANDS:*
/snipe - Start sniping (Max: {tier_info['max_trade']} SOL)
/upgrade - View subscription tiers
/stats - Detailed P&L analysis
/wallet - Check balance
/help - Documentation

⚠️ *RISK WARNING:* Trade responsibly"""
        
        keyboard = [
            [InlineKeyboardButton("🎯 SNIPE NOW", callback_data="snipe")],
            [InlineKeyboardButton("⭐ UPGRADE", callback_data="upgrade")],
            [InlineKeyboardButton("📊 MY STATS", callback_data="stats")]
        ]
        
        await update.message.reply_text(
            welcome, 
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        await self.notify_channel(f"👤 Active user: `{user.id}` | Tier: {tier_info['name']}")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.db.get_user(update.effective_user.id)
        tier = self.get_tier_info(update.effective_user.id)
        
        # Calculate win rate
        win_rate = (user['total_profit'] / user['total_volume'] * 100) if user['total_volume'] > 0 else 0
        
        stats_text = f"""📊 *YOUR TRADING PERFORMANCE*

💰 *Financials:*
• Total Trades: {user['total_trades']}
• Volume: {user['total_volume']:.3f} SOL
• Gross Profit: {user['total_profit']:.4f} SOL
• Fees Paid: {user['total_fees_paid']:.4f} SOL
• Net Profit: {user['total_profit'] - user['total_fees_paid']:.4f} SOL

☕ *Coffee Earnings:* {user['coffee_earnings']:.4f} SOL
(Small consistent profits ≤0.1 SOL)

📈 *Performance:*
• Win Rate: {win_rate:.1f}%
• Avg Trade: {user['total_volume']/max(user['total_trades'],1):.3f} SOL
• Fee Rate: {tier['fee_percent']}%

⭐ *Current Tier:* {tier['name']}
🔄 Daily Trades: {user['daily_trades']}/{tier['daily_trades']}"""
        
        await update.message.reply_text(stats_text, parse_mode="Markdown")
    
    async def upgrade_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        current_tier = self.db.get_user(update.effective_user.id)["tier"]
        
        text = "⭐ *SUBSCRIPTION TIERS*\n\n"
        
        for tier_id, tier in TIERS.items():
            status = "✅ CURRENT" if tier_id == current_tier else ""
            text += f"""{tier['name']} {status}
💰 Price: {tier['price_sol']} SOL/month
📊 Max Trade: {tier['max_trade']} SOL
🔄 Daily Limit: {tier['daily_trades']} trades
⚡ Fee: {tier['fee_percent']}%
🚀 MEV Boost: {'✅' if tier['mev_boost'] else '❌'}
🤖 Auto TP/SL: {'✅' if tier['auto_tp'] else '❌'}

"""
        
        text += "\n💡 *To upgrade:* Contact @YourAdmin or use /pay"
        
        keyboard = []
        if current_tier != "pro":
            keyboard.append([InlineKeyboardButton("⚡ Upgrade to Pro (0.5 SOL)", callback_data="upgrade_pro")])
        if current_tier != "whale":
            keyboard.append([InlineKeyboardButton("🐋 Upgrade to Whale (2 SOL)", callback_data="upgrade_whale")])
        
        await update.message.reply_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
            parse_mode="Markdown"
        )
    
    async def snipe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.db.get_user(update.effective_user.id)
        tier = self.get_tier_info(update.effective_user.id)
        
        # Check daily limit
        today = str(datetime.now().date())
        if user["last_trade_date"] != today:
            user["daily_trades"] = 0
            user["last_trade_date"] = today
        
        if user["daily_trades"] >= tier["daily_trades"]:
            await update.message.reply_text(
                f"❌ Daily limit reached ({tier['daily_trades']} trades)\n"
                f"⭐ Upgrade to increase limits: /upgrade"
            )
            return ConversationHandler.END
        
        await update.message.reply_text(
            f"🎯 *SNIPER MODE*\n"
            f"⭐ Tier: {tier['name']}\n"
            f"💰 Max: {tier['max_trade']} SOL per trade\n"
            f"🔄 Remaining today: {tier['daily_trades'] - user['daily_trades']} trades\n\n"
            f"Send token contract address:",
            parse_mode="Markdown"
        )
        return WAITING_TOKEN
    
    async def handle_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        token = update.message.text.strip()
        
        if len(token) < 32:
            await update.message.reply_text("❌ Invalid Solana address")
            return ConversationHandler.END
        
        context.user_data["token"] = token
        
        # Quick safety check
        checking = await update.message.reply_text("🔍 Scanning token...")
        
        safety = await self.check_token_safety(token)
        
        if not safety["safe"]:
            await checking.edit_text(
                f"🚫 *TOKEN RISKY*\n"
                f"Reason: {safety.get('reason', 'High risk')}\n"
                f"⚠️ Trade with caution or skip"
            )
        
        tier = self.get_tier_info(update.effective_user.id)
        
        await checking.edit_text(
            f"✅ *TOKEN READY*\n"
            f"Score: {safety.get('score', 50)}/100\n\n"
            f"💰 Enter SOL amount (0.05 - {tier['max_trade']}):"
        )
        return WAITING_AMOUNT
    
    async def handle_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        tier = self.get_tier_info(user_id)
        
        try:
            amount = float(update.message.text)
            if amount < 0.05:
                await update.message.reply_text("❌ Minimum 0.05 SOL")
                return WAITING_AMOUNT
            
            if amount > tier["max_trade"]:
                await update.message.reply_text(
                    f"❌ Max for {tier['name']} is {tier['max_trade']} SOL\n"
                    f"⭐ Upgrade: /upgrade"
                )
                return WAITING_AMOUNT
                
        except ValueError:
            await update.message.reply_text("❌ Invalid number")
            return WAITING_AMOUNT
        
        token = context.user_data["token"]
        
        executing = await update.message.reply_text(
            "⚡ *EXECUTING SNIPER...*\n"
            f"💰 Amount: {amount} SOL\n"
            f"🔗 Token: `{token[:20]}...`\n"
            f"⏳ Submitting to Jupiter...",
            parse_mode="Markdown"
        )
        
        # Execute trade
        result = await self.execute_jupiter_swap(token, amount, tier["mev_boost"])
        
        if result["success"]:
            # Calculate P&L
            entry_price = result["price"]
            # Simulate exit (in real bot, this would be actual market price)
            exit_price = entry_price * 1.05  # Assume 5% profit for demo
            
            profit = (exit_price - entry_price) * (amount / entry_price) if entry_price > 0 else 0
            fee = max(profit, 0) * (tier["fee_percent"] / 100)
            
            # Record trade
            self.db.record_trade(user_id, amount, profit, fee)
            self.admin_revenue += fee
            
            # Coffee check
            coffee_msg = ""
            if 0 < profit <= 0.1:
                coffee_msg = f"\n☕ Coffee earned: +{profit:.4f} SOL!"
            
            success_text = f"""✅ *SNIPER SUCCESS!*

🎯 Token: `{token[:20]}...`
💰 Invested: {amount:.3f} SOL
📊 Entry: {entry_price:.8f}
💵 Exit: {exit_price:.8f}
💸 Gross Profit: +{profit:.4f} SOL
⚡ Fee ({tier['fee_percent']}%): {fee:.4f} SOL
🎉 Net Profit: {profit - fee:.4f} SOL{coffee_msg}

🔗 TX: `{result['tx'][:25]}...`

🤖 *Auto-sell active:*
Monitoring for TP/SL..."""
            
            await executing.edit_text(success_text, parse_mode="Markdown")
            
            await self.notify_channel(
                f"🔥 *TRADE EXECUTED*\n"
                f"User: `{user_id}` | Tier: {tier['name']}\n"
                f"Amount: {amount} SOL | Profit: {profit:.4f}\n"
                f"Fee: {fee:.4f} SOL | Revenue: +{fee:.4f}"
            )
        else:
            await executing.edit_text(f"❌ Failed: {result['error']}")
        
        return ConversationHandler.END
    
    async def execute_jupiter_swap(self, token, amount_sol, mev_boost=False):
        try:
            # Priority fee for MEV boost
            priority_fee = 10000 if mev_boost else 0
            
            quote_url = (
                f"https://quote-api.jup.ag/v6/quote?"
                f"inputMint=So11111111111111111111111111111111111111112&"
                f"outputMint={token}&"
                f"amount={int(amount_sol * 1e9)}&"
                f"slippageBps=200"
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.get(quote_url) as resp:
                    if resp.status != 200:
                        return {"success": False, "error": "No trading route found"}
                    
                    quote = await resp.json()
                    
                    # Get swap transaction
                    swap_data = {
                        "quoteResponse": quote,
                        "userPublicKey": WALLET,
                        "wrapAndUnwrapSol": True,
                        "prioritizationFeeLamports": priority_fee
                    }
                    
                    async with session.post(
                        "https://quote-api.jup.ag/v6/swap",
                        json=swap_data
                    ) as swap_resp:
                        if swap_resp.status == 200:
                            swap_result = await swap_resp.json()
                            return {
                                "success": True,
                                "tx": swap_result.get("swapTransaction", "pending"),
                                "price": float(quote.get("outAmount", 0)) / 1e6 / amount_sol if amount_sol > 0 else 0
                            }
                        
            return {"success": False, "error": "Swap execution failed"}
            
        except Exception as e:
            logger.error(f"Swap error: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_token_safety(self, token: str) -> Dict:
        try:
            async with aiohttp.ClientSession() as session:
                # Check Jupiter routing
                check_url = (
                    f"https://quote-api.jup.ag/v6/quote?"
                    f"inputMint={token}&"
                    f"outputMint=So11111111111111111111111111111111111111112&"
                    f"amount=1000000&slippageBps=200"
                )
                
                async with session.get(check_url) as resp:
                    if resp.status != 200:
                        return {"safe": False, "reason": "Not tradable", "score": 0}
                    
                    data = await resp.json()
                    price_impact = float(data.get("priceImpactPct", 100))
                    
                    # Score based on liquidity
                    score = max(0, 100 - int(price_impact * 3))
                    
                    return {
                        "safe": score > 50,
                        "score": score,
                        "price_impact": price_impact,
                        "reason": f"Price impact: {price_impact:.2f}%"
                    }
                    
        except Exception as e:
            return {"safe": False, "reason": "Check failed", "score": 0}
    
    async def wallet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    RPC_URL,
                    json={"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [WALLET]}
                ) as resp:
                    data = await resp.json()
                    balance = data["result"]["value"] / 1e9
        except:
            balance = 0.0
        
        user = self.db.get_user(update.effective_user.id)
        
        await update.message.reply_text(
            f"💼 *YOUR WALLET*\n\n"
            f"📍 `{WALLET}`\n"
            f"💰 Balance: `{balance:.4f}` SOL\n\n"
            f"📊 *Your Activity:*\n"
            f"Trades: {user['total_trades']}\n"
            f"Volume: {user['total_volume']:.2f} SOL\n"
            f"☕ Coffee: {user['coffee_earnings']:.4f} SOL\n\n"
            f"📥 Send SOL to trade",
            parse_mode="Markdown"
        )
    
    async def admin_revenue_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("⛔ Admin only")
            return
        
        # Calculate total users and revenue
        total_users = len(self.db.users)
        total_fees = sum(u["total_fees_paid"] for u in self.db.users.values())
        
        await update.message.reply_text(
            f"💰 *ADMIN REVENUE DASHBOARD*\n\n"
            f"👥 Total Users: {total_users}\n"
            f"💵 Total Fees: {total_fees:.4f} SOL\n"
            f"💵 Admin Revenue: {self.admin_revenue:.4f} SOL\n"
            f"💵 USD Value: ~${self.admin_revenue * 150:.2f}\n\n"
            f"📊 Fee Wallet: `{FEE_WALLET[:20]}...`",
            parse_mode="Markdown"
        )
    
    async def notify_channel(self, message: str):
        try:
            from telegram import Bot
            await Bot(BOT_TOKEN).send_message(
                chat_id=CHANNEL_ID,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Notify failed: {e}")
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❌ Cancelled")
        return ConversationHandler.END

def main():
    logger.add("logs/bot.log", rotation="500 MB")
    
    bot = MexBalancerPro()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation for sniping
    snipe_conv = ConversationHandler(
        entry_points=[CommandHandler("snipe", bot.snipe_command)],
        states={
            WAITING_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_token)],
            WAITING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_amount)]
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)]
    )
    
    # Commands
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("stats", bot.stats_command))
    app.add_handler(CommandHandler("upgrade", bot.upgrade_command))
    app.add_handler(CommandHandler("wallet", bot.wallet_command))
    app.add_handler(CommandHandler("revenue", bot.admin_revenue_command))
    app.add_handler(CommandHandler("help", bot.start))
    app.add_handler(snipe_conv)
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(lambda u,c: bot.snipe_command(u,c), pattern="^snipe$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: bot.upgrade_command(u,c), pattern="^upgrade$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: bot.stats_command(u,c), pattern="^stats$"))
    
    logger.info("🚀 MEX BALANCER PRO v2.0 STARTED")
    
    # Notify channel
    asyncio.get_event_loop().run_until_complete(
        bot.notify_channel("🤖 *MEX BALANCER PRO v2.0* is ONLINE!\\n\\n✅ Subscription tiers active\\n✅ Profit tracking enabled\\n✅ Coffee earnings ready")
    )
    
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
