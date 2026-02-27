import os, sys, threading, asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.executor import executor
from modules.router import router

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ALIVE")

def run_health():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), HealthHandler)
    server.serve_forever()

async def start(u, c):
    await u.message.reply_text("🦅 **GUARDIAN ONLINE**\nUse /status to check wallet.")

async def status(u, c):
    bal = await executor.get_balance()
    await u.message.reply_text(f"📊 **WALLET:** {bal} SOL\nShield: **ACTIVE**")

async def handle(u, c):
    if len(u.message.text) >= 32:
        res = await router.secure_snipe(u.message.text)
        await u.message.reply_text(res)

def main():
    threading.Thread(target=run_health, daemon=True).start()
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    print("🚀 DEPLOYED TO HOST")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
