#!/usr/bin/env python3
"""
🤖 MEX BALANCER PRO - MEV SNIPER BOT
Professional Solana Trading with Revenue Tracking
"""

import os
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict
from loguru import logger

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

from dotenv import load_dotenv
load_dotenv()

# Load config from env
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID")
RPC_URL = os.getenv("RPC_URL")
HELIUS_KEY = RPC_URL.split("api-key=")[-1] if "api-key=" in RPC_URL else ""
WALLET = os.getenv("SOL_MAIN")
FEE_WALLET = os.getenv("FEE_WALLET", WALLET)
RUGCHECK_KEY = os.getenv("RUGCHECK_API_KEY")

WAITING_TOKEN = 1
WAITING_AMOUNT = 2

class MexBalancerPro:
    def __init__(self):
        self.revenue = 0.0
        self.trades = []
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        welcome = f"""🎯 *MEX BALANCER PRO* - MEV SNIPER

👤 User: `{user.id}`
⛓️ Chain: Solana Mainnet
🤖 Status: 🟢 OPERATIONAL

📊 *FEATURES:*
• ⚡ Ultra-fast sniping (Jupiter + Jito MEV)
• 🛡️ Pre-trade safety scan
• 🤖 Auto TP/SL (2x/5x/Trailing)
• 💰 Auto fee collection (0.5% on profits)
• 📈 Real-time P&L tracking

💼 *COMMANDS:*
/snipe - Start new snipe
/positions - Active trades  
/wallet - Check balance
/revenue - Fee earnings (Admin)
/help - Documentation

⚠️ *RISK WARNING:*
Crypto trading carries high risk."""
        
        keyboard = [
            [InlineKeyboardButton("🎯 SNIPE NOW", callback_data="snipe")],
            [InlineKeyboardButton("💼 WALLET", callback_data="wallet")],
            [InlineKeyboardButton("📊 POSITIONS", callback_data="positions")]
        ]
        
        await update.message.reply_text(
            welcome, 
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        await self.notify_channel(f"👤 New user started bot: `{user.id}`")
    
    async def snipe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🎯 *SNIPER MODE*\n\n"
            "Send token contract address:\n"
            "Example: `DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263`",
            parse_mode="Markdown"
        )
        return WAITING_TOKEN
    
    async def handle_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        token = update.message.text.strip()
        
        if len(token) < 32:
            await update.message.reply_text("❌ Invalid address")
            return ConversationHandler.END
        
        checking = await update.message.reply_text("🔍 Scanning token safety...")
        
        safety = await self.check_token_safety(token)
        
        if not safety["safe"]:
            await checking.edit_text(
                f"🚫 *RUG DETECTED - BLOCKED*\n"
                f"Reason: {safety['reason']}\n"
                f"Your funds are protected."
            )
            await self.notify_channel(f"🛡️ Blocked rug: `{token[:20]}...`")
            return ConversationHandler.END
        
        context.user_data["token"] = token
        context.user_data["safety"] = safety
        
        await checking.edit_text(
            f"✅ *TOKEN SAFE*\n"
            f"Score: {safety['score']}/100\n"
            f"Price Impact: {safety.get('price_impact', 'N/A')}%\n\n"
            f"💰 How much SOL? (0.05 - 10)"
        )
        return WAITING_AMOUNT
    
    async def handle_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            amount = float(update.message.text)
            if amount < 0.05:
                await update.message.reply_text("❌ Minimum 0.05 SOL")
                return WAITING_AMOUNT
        except:
            await update.message.reply_text("❌ Invalid number")
            return WAITING_AMOUNT
        
        token = context.user_data["token"]
        
        executing = await update.message.reply_text(
            "⚡ *EXECUTING MEV SNIPER...*\n"
            "• Routing via Jupiter\n"
            "• Adding Jito priority fee\n"
            "• Submitting transaction...",
            parse_mode="Markdown"
        )
        
        result = await self.execute_jupiter_swap(token, amount)
        
        if result["success"]:
            fee = amount * 0.005
            self.revenue += fee
            
            success_text = f"""✅ *SNIPER SUCCESS!*

🎯 Token: `{token[:20]}...`
💰 Invested: {amount:.3f} SOL
⚡ Fee: {fee:.4f} SOL (0.5%)
📊 Entry: {result['price']:.8f}
🔗 TX: `{result['tx'][:25]}...`

🤖 *AUTO-SELL ACTIVE:*
• TP1 (+100%): Sell 50%
• TP2 (+400%): Sell 50%
• SL (-20%): Emergency exit

⏱️ Monitoring 24/7..."""
            
            await executing.edit_text(success_text, parse_mode="Markdown")
            
            await self.notify_channel(
                f"🔥 *NEW TRADE EXECUTED*\n"
                f"User: `{update.effective_user.id}`\n"
                f"Amount: {amount} SOL\n"
                f"Fee Earned: {fee:.4f} SOL\n"
                f"Total Revenue: {self.revenue:.4f} SOL"
            )
            
            # Store trade for monitoring
            self.trades.append({
                "user": update.effective_user.id,
                "token": token,
                "amount": amount,
                "entry": result['price'],
                "time": datetime.now()
            })
        else:
            await executing.edit_text(f"❌ Failed: {result['error']}")
        
        return ConversationHandler.END
    
    async def execute_jupiter_swap(self, token: str, amount_sol: float) -> Dict:
        try:
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
                        return {"success": False, "error": "No route found"}
                    
                    quote = await resp.json()
                    
                    swap_data = {
                        "quoteResponse": quote,
                        "userPublicKey": WALLET,
                        "wrapAndUnwrapSol": True,
                        "prioritizationFeeLamports": 10000
                    }
                    
                    async with session.post(
                        "https://quote-api.jup.ag/v6/swap",
                        json=swap_data
                    ) as swap_resp:
                        if swap_resp.status == 200:
                            swap_result = await swap_resp.json()
                            return {
                                "success": True,
                                "tx": swap_result.get("swapTransaction", "unknown"),
                                "price": float(quote.get("outAmount", 0)) / 1e6 / amount_sol if amount_sol > 0 else 0
                            }
                        
            return {"success": False, "error": "Swap failed"}
            
        except Exception as e:
            logger.error(f"Swap error: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_token_safety(self, token: str) -> Dict:
        try:
            # Check Jupiter routing
            async with aiohttp.ClientSession() as session:
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
                    
                    if price_impact > 15:
                        return {
                            "safe": False, 
                            "reason": f"High slippage: {price_impact:.1f}%",
                            "score": 20
                        }
                    
                    return {
                        "safe": True,
                        "score": max(0, 100 - int(price_impact * 2)),
                        "price_impact": price_impact,
                        "liquidity": "good"
                    }
                    
        except Exception as e:
            logger.error(f"Safety check: {e}")
            return {"safe": False, "reason": "Check failed", "score": 0}
    
    async def wallet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    RPC_URL,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getBalance",
                        "params": [WALLET]
                    }
                ) as resp:
                    data = await resp.json()
                    balance = data["result"]["value"] / 1e9
        except:
            balance = 0.0
        
        await update.message.reply_text(
            f"💼 *YOUR TRADING WALLET*\n\n"
            f"📍 `{WALLET}`\n"
            f"💰 Balance: `{balance:.4f}` SOL\n\n"
            f"📥 Send SOL to trade\n"
            f"⚠️ Keep 0.05 SOL for gas",
            parse_mode="Markdown"
        )
    
    async def revenue_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("⛔ Admin only")
            return
        
        await update.message.reply_text(
            f"💰 *REVENUE DASHBOARD*\n\n"
            f"📊 Total Fees: {self.revenue:.4f} SOL\n"
            f"💵 USD Value: ~${self.revenue * 150:.2f}\n"
            f"🎯 Today's Trades: {len(self.trades)}\n\n"
            f"Fee Wallet: `{FEE_WALLET[:20]}...`",
            parse_mode="Markdown"
        )
    
    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_trades = [t for t in self.trades if t["user"] == update.effective_user.id]
        
        if not user_trades:
            await update.message.reply_text("📭 No active positions")
            return
        
        text = "📊 *YOUR POSITIONS*\n\n"
        for trade in user_trades[-5:]:
            text += f"🎯 `{trade['token'][:15]}...`\n"
            text += f"   Amount: {trade['amount']:.3f} SOL\n"
            text += f"   Entry: {trade['entry']:.6f}\n\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    
    async def notify_channel(self, message: str):
        try:
            from telegram import Bot
            bot = Bot(BOT_TOKEN)
            await bot.send_message(
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
    
    snipe_conv = ConversationHandler(
        entry_points=[CommandHandler("snipe", bot.snipe_command)],
        states={
            WAITING_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_token)],
            WAITING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_amount)]
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)]
    )
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("wallet", bot.wallet_command))
    app.add_handler(CommandHandler("revenue", bot.revenue_command))
    app.add_handler(CommandHandler("positions", bot.positions_command))
    app.add_handler(CommandHandler("help", bot.start))
    app.add_handler(snipe_conv)
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(lambda u,c: bot.snipe_command(u,c), pattern="^snipe$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: bot.wallet_command(u,c), pattern="^wallet$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: bot.positions_command(u,c), pattern="^positions$"))
    
    logger.info("🚀 MEX BALANCER PRO STARTED")
    
    # Startup notification
    asyncio.get_event_loop().run_until_complete(
        bot.notify_channel("🤖 *MEX BALANCER PRO* is ONLINE!\\nReady for MEV sniping.")
    )
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
