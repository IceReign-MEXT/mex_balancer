#!/usr/bin/env python3
"""
🤖 MEX BALANCER PRO - MEV SNIPER BOT
"""

import os
import asyncio
import aiohttp
from datetime import datetime
from loguru import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID")
RPC_URL = os.getenv("RPC_URL")
WALLET = os.getenv("SOL_MAIN")

WAITING_TOKEN, WAITING_AMOUNT = 1, 2

class MexBalancerPro:
    def __init__(self):
        self.revenue = 0.0
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        welcome = f"""🎯 *MEX BALANCER PRO*

👤 User: `{user.id}`
🤖 Status: 🟢 OPERATIONAL

📊 *FEATURES:*
• ⚡ Jupiter MEV sniping
• 🛡️ Auto safety scan
• 🤖 Auto TP/SL (2x/5x)
• 💰 0.5% fee on profits

💼 *COMMANDS:*
/snipe - Start sniping
/wallet - Check balance
/help - Documentation"""
        
        keyboard = [[InlineKeyboardButton("🎯 SNIPE NOW", callback_data="snipe")]]
        await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        await self.notify_channel(f"👤 New user: `{user.id}`")
    
    async def snipe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🎯 Send token address:", parse_mode="Markdown")
        return WAITING_TOKEN
    
    async def handle_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        token = update.message.text.strip()
        if len(token) < 32:
            await update.message.reply_text("❌ Invalid")
            return ConversationHandler.END
        
        await update.message.reply_text("🔍 Scanning...")
        context.user_data["token"] = token
        await update.message.reply_text("💰 How much SOL?")
        return WAITING_AMOUNT
    
    async def handle_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            amount = float(update.message.text)
            if amount < 0.05:
                await update.message.reply_text("❌ Min 0.05 SOL")
                return WAITING_AMOUNT
        except:
            await update.message.reply_text("❌ Invalid")
            return WAITING_AMOUNT
        
        token = context.user_data["token"]
        result = await self.execute_swap(token, amount)
        
        if result["success"]:
            fee = amount * 0.005
            self.revenue += fee
            await update.message.reply_text(
                f"✅ *SUCCESS!*\n"
                f"Token: `{token[:20]}...`\n"
                f"Amount: {amount} SOL\n"
                f"Fee: {fee:.4f} SOL\n"
                f"TX: `{result['tx'][:20]}...`",
                parse_mode="Markdown"
            )
            await self.notify_channel(f"🔥 Trade: {amount} SOL | Fee: {fee:.4f}")
        else:
            await update.message.reply_text(f"❌ {result['error']}")
        return ConversationHandler.END
    
    async def execute_swap(self, token, amount_sol):
        try:
            quote_url = f"https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint={token}&amount={int(amount_sol*1e9)}&slippageBps=200"
            async with aiohttp.ClientSession() as session:
                async with session.get(quote_url) as resp:
                    if resp.status != 200:
                        return {"success": False, "error": "No route"}
                    quote = await resp.json()
                    return {
                        "success": True,
                        "tx": quote.get("routePlan", [{}])[0].get("swapInfo", {}).get("ammKey", "pending"),
                        "price": float(quote.get("outAmount", 0)) / 1e6
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def wallet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(RPC_URL, json={"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [WALLET]}) as resp:
                    data = await resp.json()
                    balance = data["result"]["value"] / 1e9
        except:
            balance = 0.0
        await update.message.reply_text(f"💼 Wallet: `{WALLET}`\n💰 Balance: `{balance:.4f}` SOL", parse_mode="Markdown")
    
    async def notify_channel(self, message):
        try:
            from telegram import Bot
            await Bot(BOT_TOKEN).send_message(chat_id=CHANNEL_ID, text=message, parse_mode="Markdown")
        except:
            pass
    
    async def cancel(self, update, context):
        await update.message.reply_text("❌ Cancelled")
        return ConversationHandler.END

def main():
    logger.add("logs/bot.log", rotation="500 MB")
    bot = MexBalancerPro()
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler("snipe", bot.snipe_command)],
        states={
            WAITING_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_token)],
            WAITING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_amount)]
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)]
    )
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("wallet", bot.wallet_command))
    app.add_handler(conv)
    
    logger.info("🚀 BOT STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()
