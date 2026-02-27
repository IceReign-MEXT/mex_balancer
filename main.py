import os, sys, logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup environment
load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
from modules.router import router

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦅 **ICEBOYS GUARDIAN V2.0**\n\nStatus: **ARMED**\nWallet: **SECURE**")

async def handle_msg(update, context):
    text = update.message.text
    if text and len(text) >= 32:
        res = await router.secure_snipe(text)
        await update.message.reply_text(res)

def main():
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print("🚀 GUARDIAN BOOTED")
    app.run_polling()

if __name__ == "__main__":
    main()
