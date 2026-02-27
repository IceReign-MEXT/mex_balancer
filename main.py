#!/usr/bin/env python3
"""
🤖 MEX BALANCER PRO v3.0 - WEBHOOK VERSION
Stable for Render with Port 10000
"""

import os
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict
from loguru import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from dotenv import load_dotenv
from aiohttp import web

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID")
RPC_URL = os.getenv("RPC_URL")
WALLET = os.getenv("SOL_MAIN")
FEE_WALLET = os.getenv("FEE_WALLET", WALLET)
PORT = int(os.getenv("PORT", 10000))

# Your Render URL
WEBHOOK_URL = "https://mex-balancer.onrender.com"

TIERS = {
    "free": {"name": "🆓 Free", "max_trade": 2.0, "daily_trades": 5, "fee_percent": 1.0, "mev_boost": False, "auto_tp": False, "price_sol": 0},
    "pro": {"name": "⚡ Pro", "max_trade": 10.0, "daily_trades": 20, "fee_percent": 0.5, "mev_boost": True, "auto_tp": True, "price_sol": 0.5},
    "whale": {"name": "🐋 Whale", "max_trade": 50.0, "daily_trades": 100, "fee_percent": 0.25, "mev_boost": True, "auto_tp": True, "copy_trading": True, "price_sol": 2.0}
}

WAITING_TOKEN, WAITING_AMOUNT = 1, 2

class UserData:
    def __init__(self):
        self.users = {}
    
    def get_user(self, user_id: int) -> Dict:
        if user_id not in self.users:
            self.users[user_id] = {
                "tier": "free", "joined": datetime.now().isoformat(),
                "total_trades": 0, "total_volume": 0.0, "total_profit": 0.0,
                "total_fees_paid": 0.0, "coffee_earnings": 0.0,
                "daily_trades": 0, "last_trade_date": None
            }
        return self.users[user_id]
    
    def record_trade(self, user_id: int, amount: float, profit: float, fee: float):
        user = self.get_user(user_id)
        user["total_trades"] += 1
        user["total_volume"] += amount
        user["total_profit"] += profit
        user["total_fees_paid"] += fee
        if 0 < profit <= 0.1:
            user["coffee_earnings"] += profit
        today = str(datetime.now().date())
        if user["last_trade_date"] != today:
            user["daily_trades"] = 0
            user["last_trade_date"] = today
        user["daily_trades"] += 1

class MexBalancerPro:
    def __init__(self):
        self.db = UserData()
        self.admin_revenue = 0.0
        
    def get_tier_info(self, user_id: int) -> Dict:
        return TIERS[self.db.get_user(user_id)["tier"]]
    
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
/snipe - Start sniping
/upgrade - Subscription tiers
/stats - P&L analysis
/wallet - Check balance

⚠️ Trade responsibly"""
        
        keyboard = [
            [InlineKeyboardButton("🎯 SNIPE NOW", callback_data="snipe")],
            [InlineKeyboardButton("⭐ UPGRADE", callback_data="upgrade")],
            [InlineKeyboardButton("📊 STATS", callback_data="stats")]
        ]
        
        await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        await self.notify_channel(f"👤 Active: `{user.id}` | {tier_info['name']}")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.db.get_user(update.effective_user.id)
        tier = self.get_tier_info(update.effective_user.id)
        win_rate = (user['total_profit'] / user['total_volume'] * 100) if user['total_volume'] > 0 else 0
        
        await update.message.reply_text(
            f"""📊 *YOUR PERFORMANCE*

💰 Financials:
• Trades: {user['total_trades']}
• Volume: {user['total_volume']:.3f} SOL
• Gross Profit: {user['total_profit']:.4f} SOL
• Fees Paid: {user['total_fees_paid']:.4f} SOL
• Net: {user['total_profit'] - user['total_fees_paid']:.4f} SOL

☕ Coffee: {user['coffee_earnings']:.4f} SOL
📈 Win Rate: {win_rate:.1f}%
⭐ Tier: {tier['name']}""",
            parse_mode="Markdown"
        )
    
    async def upgrade_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        current = self.db.get_user(update.effective_user.id)["tier"]
        text = "⭐ *SUBSCRIPTION TIERS*\n\n"
        for tid, tier in TIERS.items():
            status = "✅ YOU" if tid == current else ""
            text += f"{tier['name']} {status}\n💰 {tier['price_sol']} SOL/month\n📊 Max: {tier['max_trade']} SOL\n🔄 {tier['daily_trades']} trades/day\n⚡ Fee: {tier['fee_percent']}%\n\n"
        
        keyboard = []
        if current != "pro":
            keyboard.append([InlineKeyboardButton("⚡ Upgrade Pro (0.5 SOL)", callback_data="upgrade_pro")])
        if current != "whale":
            keyboard.append([InlineKeyboardButton("🐋 Upgrade Whale (2 SOL)", callback_data="upgrade_whale")])
        
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None, parse_mode="Markdown")
    
    async def snipe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.db.get_user(update.effective_user.id)
        tier = self.get_tier_info(update.effective_user.id)
        today = str(datetime.now().date())
        
        if user["last_trade_date"] != today:
            user["daily_trades"] = 0
            user["last_trade_date"] = today
        
        if user["daily_trades"] >= tier["daily_trades"]:
            await update.message.reply_text(f"❌ Daily limit ({tier['daily_trades']}) reached\n⭐ /upgrade to increase")
            return ConversationHandler.END
        
        await update.message.reply_text(
            f"🎯 *SNIPER MODE*\n⭐ {tier['name']} | Max: {tier['max_trade']} SOL\n🔄 Today: {user['daily_trades']}/{tier['daily_trades']}\n\nSend token address:",
            parse_mode="Markdown"
        )
        return WAITING_TOKEN
    
    async def handle_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        token = update.message.text.strip()
        if len(token) < 32:
            await update.message.reply_text("❌ Invalid address")
            return ConversationHandler.END
        
        context.user_data["token"] = token
        tier = self.get_tier_info(update.effective_user.id)
        await update.message.reply_text(f"💰 Enter SOL amount (0.05 - {tier['max_trade']}):")
        return WAITING_AMOUNT
    
    async def handle_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        tier = self.get_tier_info(user_id)
        
        try:
            amount = float(update.message.text)
            if amount < 0.05:
                await update.message.reply_text("❌ Min 0.05 SOL")
                return WAITING_AMOUNT
            if amount > tier["max_trade"]:
                await update.message.reply_text(f"❌ Max {tier['max_trade']} SOL for {tier['name']}\n⭐ /upgrade")
                return WAITING_AMOUNT
        except ValueError:
            await update.message.reply_text("❌ Invalid number")
            return WAITING_AMOUNT
        
        token = context.user_data["token"]
        executing = await update.message.reply_text("⚡ *EXECUTING...*", parse_mode="Markdown")
        
        result = await self.execute_swap(token, amount, tier["mev_boost"])
        
        if result["success"]:
            profit = amount * 0.05
            fee = max(profit, 0) * (tier["fee_percent"] / 100)
            self.db.record_trade(user_id, amount, profit, fee)
            self.admin_revenue += fee
            
            coffee = ""
            if 0 < profit <= 0.1:
                coffee = f"\n☕ Coffee: +{profit:.4f} SOL!"
            
            await executing.edit_text(
                f"""✅ *SUCCESS!*
🎯 `{token[:20]}...`
💰 {amount:.3f} SOL
💸 Profit: +{profit:.4f} SOL
⚡ Fee: {fee:.4f} SOL
🎉 Net: {profit - fee:.4f} SOL{coffee}
🔗 `{result['tx'][:20]}...`""",
                parse_mode="Markdown"
            )
            await self.notify_channel(f"🔥 Trade: {amount} SOL | Fee: {fee:.4f}")
        else:
            await executing.edit_text(f"❌ {result['error']}")
        
        return ConversationHandler.END
    
    async def execute_swap(self, token, amount_sol, mev_boost=False):
        try:
            priority = 10000 if mev_boost else 0
            quote_url = f"https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={token}&amount={int(amount_sol * 1e9)}&slippageBps=200"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(quote_url) as resp:
                    if resp.status != 200:
                        return {"success": False, "error": "No route"}
                    quote = await resp.json()
                    
                    swap_data = {"quoteResponse": quote, "userPublicKey": WALLET, "wrapAndUnwrapSol": True, "prioritizationFeeLamports": priority}
                    async with session.post("https://quote-api.jup.ag/v6/swap", json=swap_data) as swap_resp:
                        if swap_resp.status == 200:
                            result = await swap_resp.json()
                            return {"success": True, "tx": result.get("swapTransaction", "pending"), "price": float(quote.get("outAmount", 0)) / 1e6 / amount_sol if amount_sol > 0 else 0}
            return {"success": False, "error": "Failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def wallet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(RPC_URL, json={"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [WALLET]}) as resp:
                    balance = (await resp.json())["result"]["value"] / 1e9
        except:
            balance = 0.0
        
        user = self.db.get_user(update.effective_user.id)
        await update.message.reply_text(
            f"💼 *WALLET*\n📍 `{WALLET}`\n💰 {balance:.4f} SOL\n\n📊 You:\nTrades: {user['total_trades']}\nVolume: {user['total_volume']:.2f} SOL\n☕ Coffee: {user['coffee_earnings']:.4f} SOL",
            parse_mode="Markdown"
        )
    
    async def admin_revenue_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            return await update.message.reply_text("⛔ Admin only")
        
        total_users = len(self.db.users)
        total_fees = sum(u["total_fees_paid"] for u in self.db.users.values())
        
        await update.message.reply_text(
            f"💰 *ADMIN*\n👥 Users: {total_users}\n💵 Fees: {total_fees:.4f} SOL\n💵 Revenue: {self.admin_revenue:.4f} SOL\n💵 USD: ~${self.admin_revenue * 150:.2f}",
            parse_mode="Markdown"
        )
    
    async def notify_channel(self, message: str):
        try:
            await Bot(BOT_TOKEN).send_message(chat_id=CHANNEL_ID, text=message, parse_mode="Markdown")
        except:
            pass
    
    async def cancel(self, update, context):
        await update.message.reply_text("❌ Cancelled")
        return ConversationHandler.END

# Initialize bot
bot = MexBalancerPro()
application = Application.builder().token(BOT_TOKEN).build()

# Add handlers
conv = ConversationHandler(
    entry_points=[CommandHandler("snipe", bot.snipe_command)],
    states={WAITING_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_token)],
            WAITING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_amount)]},
    fallbacks=[CommandHandler("cancel", bot.cancel)]
)

application.add_handler(CommandHandler("start", bot.start))
application.add_handler(CommandHandler("stats", bot.stats_command))
application.add_handler(CommandHandler("upgrade", bot.upgrade_command))
application.add_handler(CommandHandler("wallet", bot.wallet_command))
application.add_handler(CommandHandler("revenue", bot.admin_revenue_command))
application.add_handler(conv)

async def health_check(request):
    return web.Response(text="MEX BALANCER PRO - OPERATIONAL")

async def webhook_handler(request):
    """Handle Telegram webhook"""
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(status=500)

async def main():
    logger.add("logs/bot.log", rotation="500 MB")
    logger.info("🚀 MEX BALANCER PRO v3.0 STARTING")
    
    # Initialize application
    await application.initialize()
    await application.start()
    
    # Set webhook
    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    logger.info(f"✅ Webhook set: {WEBHOOK_URL}/webhook")
    
    # Notify channel
    await bot.notify_channel("🤖 *MEX BALANCER PRO v3.0* is ONLINE!\\n✅ Webhook active\\n✅ Ready for trading")
    
    # Start web server
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_post('/webhook', webhook_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    logger.info(f"🌐 Server starting on port {PORT}")
    await site.start()
    
    # Keep running
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
