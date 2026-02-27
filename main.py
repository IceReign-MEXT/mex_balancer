import os, sys, logging, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
from modules.router import router

# --- HEARTBEAT SERVER FOR RENDER/UPTIMEROBOT ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ALIVE")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"📡 Heartbeat server listening on port {port}")
    server.serve_forever()

# --- BOT LOGIC ---
async def start(update, context):
    await update.message.reply_text("🦅 **ICEBOYS GUARDIAN V2.0**\n\nStatus: **ARMED**\nHealth: **STABLE**")

async def handle_msg(update, context):
    if len(update.message.text) >= 32:
        res = await router.secure_snipe(update.message.text)
        await update.message.reply_text(res)

def main():
    # Start Heartbeat in a separate thread
    threading.Thread(target=run_health_server, daemon=True).start()

    # Start Telegram Bot
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    print("🚀 GUARDIAN BOOTED")
    app.run_polling()

if __name__ == "__main__":
    main()
