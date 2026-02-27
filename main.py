import os, sys, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.executor import executor
from modules.router import router

# --- HEALTH CHECK (For Render/UptimeRobot) ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ALIVE")

def run_health():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

# --- COMMANDS ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦅 **ICEBOYS GUARDIAN V2.0**\n\nStatus: **ARMED**\nHealth: **STABLE**")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = await executor.get_balance()
    await update.message.reply_text(f"📊 **STATS**\n\nBalance: **{bal} SOL**\nTarget: **$10 Profit Mission**")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ **SETTINGS**\n\nSlippage: **15%**\nSecurity: **RugCheck High**")

async def panic_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    safe_wallet = os.getenv("SOL_MAIN")
    await update.message.reply_text(f"⚠️ **PANIC:** Routing funds to:\n`{safe_wallet}`")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only process if it's a long string (like a Contract Address)
    if len(update.message.text) >= 32:
        res = await router.secure_snipe(update.message.text)
        await update.message.reply_text(res)

def main():
    # Start the "Heartbeat" thread
    threading.Thread(target=run_health, daemon=True).start()
    
    # Initialize Bot
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    
    # IMPORTANT: Commands must come BEFORE MessageHandlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("panic", panic_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🚀 GUARDIAN V2.0 LIVE ON HOST")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
