import os, sys, logging, threading, asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
from core.executor import executor
from modules.router import router

# --- HEARTBEAT SERVER ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ALIVE")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- HANDLERS ---
async def start(update, context):
    await update.message.reply_text("🦅 **ICEBOYS GUARDIAN V2.0**\nStatus: **ARMED**\n\nPaste a CA to begin.")

async def get_status(update, context):
    bal = await executor.get_balance()
    await update.message.reply_text(f"📊 **ICEBOYS STATS**\n\nWallet Balance: **{bal} SOL**\nShield: **ACTIVE**")

async def handle_msg(update, context):
    if update.message.text and len(update.message.text) >= 32:
        res = await router.secure_snipe(update.message.text)
        await update.message.reply_text(res)

def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # Building the app with 'drop_pending_updates' to clear conflict
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", get_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    print("🚀 GUARDIAN ONLINE")
    # drop_pending_updates=True is the key to fixing the Conflict error
    app.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == "__main__":
    main()
