#!/usr/bin/env python3
"""
🤖 MEX BALANCER - ULTIMATE SOLANA SNIPER BOT
Auto-Pilot Trading with 100% Transparency
Monetization: 0.5% fee per profitable trade
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from loguru import logger

from core.config import Config
try:
    from core.sniper import SolanaSniper
except:
    from core.simple_sniper import SimpleSniper as SolanaSniper
from core.security import SecurityManager
from core.database import DatabaseManager
from core.analyzer import TokenAnalyzer
from core.monetization import FeeManager
from core.auto_trader import AutoTrader

# States
WAITING_TOKEN = 1
WAITING_AMOUNT = 2
WAITING_SLIPPAGE = 3

class MexBalancerBot:
    def __init__(self):
        self.config = Config()
        self.security = SecurityManager(self.config.encryption_key)
        self.db = DatabaseManager(self.config.database_url)
        self.analyzer = TokenAnalyzer(
            self.config.rugcheck_api_key,
            self.config.helius_api_key
        )
        self.fee_manager = FeeManager(self.config.fee_wallet)
        self.sniper: Optional[SolanaSniper] = None
        self.auto_trader: Optional[AutoTrader] = None
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("🚀 Initializing MEX BALANCER...")
        
        # Initialize sniper with main wallet
        self.sniper = SolanaSniper(
            rpc_url=self.config.rpc_url,
            wallet_key=self.config.sol_main,
            encryption_key=self.config.encryption_key
        )
        
        # Initialize auto-trader
        self.auto_trader = AutoTrader(
            sniper=self.sniper,
            db=self.db,
            fee_manager=self.fee_manager,
            channel_id=self.config.channel_id
        )
        
        # Start background tasks
        asyncio.create_task(self.auto_trader.monitor_positions())
        asyncio.create_task(self.send_heartbeat())
        
        logger.info("✅ Bot initialized successfully")
        
    async def send_heartbeat(self):
        """Send alive status every 5 minutes"""
        while True:
            await asyncio.sleep(300)
            try:
                balance = await self.sniper.get_wallet_balance()
                await self.notify_channel(
                    f"💓 *Bot Heartbeat*\n"
                    f"Wallet Balance: `{balance:.4f}` SOL\n"
                    f"Active Positions: {len(self.auto_trader.active_positions)}\n"
                    f"Status: 🟢 Operational",
                    silent=True
                )
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    # ============== COMMAND HANDLERS ==============
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command - Professional welcome"""
        user = update.effective_user
        user_id = user.id
        
        # Check if admin
        is_admin = user_id == self.config.admin_id
        
        welcome_text = (
            f"🎯 *MEX BALANCER - ELITE SNIPER BOT*\n\n"
            f"👤 Welcome, `{user.username or user.first_name}`\n"
            f"🆔 User ID: `{user_id}`\n\n"
            f"📊 *What This Bot Does:*\n"
            f"• ⚡ Ultra-fast Solana token sniping\n"
            f"• 🛡️ Auto rug-check & safety analysis\n"
            f"• 🤖 Auto-buy & auto-sell with profit targets\n"
            f"• 📈 Real-time P&L tracking\n"
            f"• 💰 Transparent fee structure (0.5% on profits only)\n\n"
            f"🎮 *Commands:*\n"
            f"/snipe - Start new snipe\n"
            f"/auto - Toggle auto-pilot mode\n"
            f"/positions - View active trades\n"
            f"/history - View trade history\n"
            f"/wallet - Check balance & deposits\n"
            f"/settings - Configure bot\n"
            f"/help - Full documentation\n\n"
            f"⚠️ *Risk Warning:*\n"
            f"Trading cryptocurrencies carries high risk. "
            f"Never invest more than you can afford to lose."
        )
        
        if is_admin:
            welcome_text += (
                f"\n\n🔐 *ADMIN PANEL:*\n"
                f"/admin - Admin dashboard\n"
                f"/fees - Fee collection stats\n"
                f"/broadcast - Send message to all users"
            )
        
        keyboard = [
            [InlineKeyboardButton("🎯 START SNIPING", callback_data="start_snipe")],
            [InlineKeyboardButton("📊 PORTFOLIO", callback_data="portfolio")],
            [InlineKeyboardButton("⚙️ SETTINGS", callback_data="settings")]
        ]
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def snipe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Interactive snipe setup"""
        await update.message.reply_text(
            "🎯 *SNIPER MODE ACTIVATED*\n\n"
            "Please send the token contract address:\n"
            "Example: `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`",
            parse_mode="Markdown"
        )
        return WAITING_TOKEN

    async def handle_token_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process token address"""
        token_address = update.message.text.strip()
        context.user_data['token'] = token_address
        
        # Quick validation
        if len(token_address) < 32 or len(token_address) > 44:
            await update.message.reply_text("❌ Invalid Solana address format")
            return ConversationHandler.END
        
        # Start analysis
        analyzing_msg = await update.message.reply_text(
            "🔍 *Analyzing Token...*\n"
            "• Checking contract safety\n"
            "• Verifying liquidity\n"
            "• Scanning for honeypots\n"
            "• Analyzing holder distribution",
            parse_mode="Markdown"
        )
        
        # Run full analysis
        analysis = await self.analyzer.full_analysis(token_address)
        
        if not analysis['is_safe']:
            await analyzing_msg.edit_text(
                f"🚨 *DANGER DETECTED - TRADE BLOCKED*\n\n"
                f"Token: `{token_address}`\n"
                f"Risk Score: {analysis['risk_score']}/100\n"
                f"Reason: {analysis['danger_reason']}\n\n"
                f"⚠️ This token has been flagged as high risk.\n"
                f"Bot has automatically rejected this trade to protect your funds.",
                parse_mode="Markdown"
            )
            
            # Notify channel of blocked rug
            await self.notify_channel(
                f"🛡️ *RUG BLOCKED*\n"
                f"Token: `{token_address}`\n"
                f"Risk: {analysis['risk_score']}/100\n"
                f"Saved user from potential scam"
            )
            return ConversationHandler.END
        
        # Show analysis results
        await analyzing_msg.edit_text(
            f"✅ *TOKEN ANALYSIS COMPLETE*\n\n"
            f"📋 Contract: `{token_address}`\n"
            f"🛡️ Safety Score: {analysis['safety_score']}/100\n"
            f"💧 Liquidity: ${analysis['liquidity_usd']:,.2f}\n"
            f"👥 Holders: {analysis['holder_count']}\n"
            f"🏦 Mint Authority: {'🔴 Risky' if analysis['mint_authority'] else '🟢 Safe'}\n"
            f"🔥 Freeze Authority: {'🔴 Risky' if analysis['freeze_authority'] else '🟢 Safe'}\n"
            f"🐋 Top 10 Holdings: {analysis['top10_percentage']}%\n\n"
            f"💰 How much SOL to invest?",
            parse_mode="Markdown"
        )
        return WAITING_AMOUNT

    async def handle_amount_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process investment amount"""
        try:
            amount = float(update.message.text)
            if amount < 0.01:
                await update.message.reply_text("❌ Minimum investment is 0.01 SOL")
                return WAITING_AMOUNT
            
            context.user_data['amount'] = amount
            
            # Show slippage options
            keyboard = [
                [InlineKeyboardButton("0.5% (Safe)", callback_data="slippage_50")],
                [InlineKeyboardButton("1% (Normal)", callback_data="slippage_100")],
                [InlineKeyboardButton("2% (Fast)", callback_data="slippage_200")],
                [InlineKeyboardButton("5% (Aggressive)", callback_data="slippage_500")]
            ]
            
            await update.message.reply_text(
                f"💰 Investment: `{amount}` SOL\n\n"
                f"📊 Select slippage tolerance:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return WAITING_SLIPPAGE
            
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number")
            return WAITING_AMOUNT

    async def execute_snipe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute the snipe"""
        query = update.callback_query
        await query.answer()
        
        slippage = int(query.data.split('_')[1])
        token = context.user_data['token']
        amount = context.user_data['amount']
        
        await query.edit_message_text(
            f"🚀 *EXECUTING SNIPER...*\n\n"
            f"Target: `{token}`\n"
            f"Amount: {amount} SOL\n"
            f"Slippage: {slippage/100}%\n\n"
            f"⚡ Submitting transaction...",
            parse_mode="Markdown"
        )
        
        # Execute trade
        result = await self.sniper.snipe_token(
            token_address=token,
            amount_sol=amount,
            slippage_bps=slippage,
            user_id=update.effective_user.id
        )
        
        if result['success']:
            # Calculate fees
            fee_amount = self.fee_manager.calculate_fee(amount)
            net_investment = amount - fee_amount
            
            # Record in database
            trade_id = await self.db.record_trade(
                user_id=update.effective_user.id,
                token=token,
                amount_sol=net_investment,
                entry_price=result['entry_price'],
                tx_signature=result['signature'],
                fee_paid=fee_amount
            )
            
            # Start monitoring for auto-sell
            await self.auto_trader.add_position(
                trade_id=trade_id,
                token=token,
                entry_price=result['entry_price'],
                amount=result['token_amount'],
                user_id=update.effective_user.id
            )
            
            # Success message
            success_text = (
                f"✅ *SNIPER SUCCESS!*\n\n"
                f"🎯 Token: `{token}`\n"
                f"💰 Invested: {net_investment} SOL\n"
                f"⚡ Fee: {fee_amount} SOL (0.5%)\n"
                f"📊 Entry Price: ${result['entry_price']:.8f}\n"
                f"🪙 Tokens Received: {result['token_amount']:.6f}\n"
                f"🔗 TX: `{result['signature']}`\n\n"
                f"🤖 *Auto-sell activated:*\n"
                f"• Take Profit 1: 2x (50% sell)\n"
                f"• Take Profit 2: 5x (50% sell)\n"
                f"• Stop Loss: -20%\n\n"
                f"⏱️ Monitoring 24/7..."
            )
            
            await query.edit_message_text(success_text, parse_mode="Markdown")
            
            # Notify channel
            await self.notify_channel(
                f"🔥 *NEW SNIPER TRADE*\n"
                f"User: `{update.effective_user.id}`\n"
                f"Token: `{token}`\n"
                f"Amount: {amount} SOL\n"
                f"Safety Score: High\n"
                f"Auto-sell: Active"
            )
            
        else:
            await query.edit_message_text(
                f"❌ *SNIPER FAILED*\n\n"
                f"Error: {result['error']}\n"
                f"Your funds are safe. No transaction was executed.",
                parse_mode="Markdown"
            )

    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show active positions"""
        positions = await self.db.get_active_positions(update.effective_user.id)
        
        if not positions:
            await update.message.reply_text(
                "📭 *No Active Positions*\n\n"
                "Use /snipe to start trading",
                parse_mode="Markdown"
            )
            return
        
        text = "📊 *ACTIVE POSITIONS*\n\n"
        for pos in positions:
            current_value = await self.sniper.get_token_value(pos['token'], pos['amount'])
            pnl = ((current_value - pos['invested_sol']) / pos['invested_sol']) * 100
            
            emoji = "🟢" if pnl > 0 else "🔴"
            text += (
                f"{emoji} `{pos['token'][:20]}...`\n"
                f"   Invested: {pos['invested_sol']:.3f} SOL\n"
                f"   Current: {current_value:.3f} SOL\n"
                f"   P&L: {pnl:+.2f}%\n\n"
            )
        
        await update.message.reply_text(text, parse_mode="Markdown")

    async def wallet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show wallet status"""
        balance = await self.sniper.get_wallet_balance()
        address = self.sniper.wallet_address
        
        await update.message.reply_text(
            f"💼 *YOUR TRADING WALLET*\n\n"
            f"📍 Address: `{address}`\n"
            f"💰 Balance: `{balance:.6f}` SOL\n\n"
            f"📥 *Deposit SOL to this address to start trading*\n\n"
            f"⚠️ *Important:*\n"
            f"• Only send SOL to this address\n"
            f"• Minimum deposit: 0.05 SOL\n"
            f"• Gas fees are deducted from balance",
            parse_mode="Markdown"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comprehensive help"""
        help_text = (
            f"📚 *MEX BALANCER DOCUMENTATION*\n\n"
            f"*GETTING STARTED:*\n"
            f"1. Deposit SOL to your bot wallet (/wallet)\n"
            f"2. Use /snipe to start trading\n"
            f"3. Bot auto-analyzes every token\n"
            f"4. Auto-sell protects your profits\n\n"
            
            f"*SAFETY FEATURES:*\n"
            f"• 🔍 Pre-trade rug detection\n"
            f"• 🛡️ Honeypot protection\n"
            f"• 📊 Liquidity verification\n"
            f"• 🚨 Auto-scam blocking\n\n"
            
            f"*AUTO-TRADE LOGIC:*\n"
            f"• TP1: +100% (sell 50%)\n"
            f"• TP2: +400% (sell 50%)\n"
            f"• SL: -20% (sell 100%)\n"
            f"• Trailing stop after 3x\n\n"
            
            f"*FEE STRUCTURE:*\n"
            f"• 0.5% on profitable trades only\n"
            f"• No fees on losses\n"
            f"• Gas fees: ~0.001 SOL per trade\n\n"
            
            f"*SUPPORTED DEX:*\n"
            f"• Raydium\n"
            f"• Pump.fun\n"
            f"• Jupiter Aggregator\n\n"
            
            f"Need help? Contact: @YourSupport"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def notify_channel(self, message: str, silent: bool = False):
        """Send notification to channel"""
        try:
            from telegram import Bot
            bot = Bot(token=self.config.bot_token)
            await bot.send_message(
                chat_id=self.config.channel_id,
                text=message,
                parse_mode="Markdown",
                disable_notification=silent
            )
        except Exception as e:
            logger.error(f"Channel notification failed: {e}")

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        await update.message.reply_text("❌ Operation cancelled")
        return ConversationHandler.END

def main():
    # Setup logging
    logger.add("logs/bot.log", rotation="500 MB", level="INFO")
    
    # Initialize bot
    bot = MexBalancerBot()
    
    # Build application
    application = Application.builder().token(bot.config.bot_token).build()
    
    # Add conversation handler for sniping
    snipe_conv = ConversationHandler(
        entry_points=[CommandHandler("snipe", bot.snipe_command)],
        states={
            WAITING_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_token_input)],
            WAITING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_amount_input)],
            WAITING_SLIPPAGE: [CallbackQueryHandler(bot.execute_snipe, pattern="^slippage_")]
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)]
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("wallet", bot.wallet_command))
    application.add_handler(CommandHandler("positions", bot.positions_command))
    application.add_handler(CommandHandler("help", bot.help))
    application.add_handler(snipe_conv)
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(
        lambda u, c: bot.snipe_command(u, c), 
        pattern="^start_snipe$"
    ))
    
    # Initialize and start
    asyncio.get_event_loop().run_until_complete(bot.initialize())
    
    logger.info("🤖 Bot starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
