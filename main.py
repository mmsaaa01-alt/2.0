# main.py
import logging
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram.request import HTTPXRequest
from config import BOT_TOKEN, ADMIN_CHAT_ID, BACKUP_CHAT_ID
from handlers import (
    start_command, status_command, curriculum_command,
    what_to_study_command, calendar_command, button_callback
)
from scheduler import setup_scheduler
from cloud_backup import restore_from_telegram, backup_loop, backup_command, id_command
from shorties import shorties_command, shorties_callback

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- Flask Server for UptimeRobot ---
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "🤖 Ethiopian Student Speedrun Bot is alive and running!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=8080)
# ------------------------------------

async def post_init(application):
    if BACKUP_CHAT_ID:
        ok = await restore_from_telegram(application.bot, BACKUP_CHAT_ID)
        print("🗄️ Restored progress from Telegram vault!" if ok else "🗄️ No backup found yet (first run).")
        
        # Start the asyncio backup loop in the background (Runs every 1 hour)
        asyncio.create_task(backup_loop(application.bot, BACKUP_CHAT_ID))
        print("🗄️ Auto-backup loop started.")

def main():
    # Start Flask web server in a separate daemon thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌍 Flask web server started on port 8080...")

    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()
    app.post_init = post_init

    # --- 1. Register Commands ---
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("curriculum", curriculum_command))
    app.add_handler(CommandHandler("what_to_study", what_to_study_command))
    app.add_handler(CommandHandler("whattostudy", what_to_study_command))
    app.add_handler(CommandHandler("calendar", calendar_command))
    app.add_handler(CommandHandler("backup", backup_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("shorties", shorties_command))

    # --- 2. Register Callback Handlers (ORDER MATTERS!) ---
    
    # MUST BE FIRST: Catches any button click starting with "shorties_"
    app.add_handler(CallbackQueryHandler(shorties_callback, pattern="^shorties_"))
    
    # SECOND: Catches all other button clicks for the main curriculum
    app.add_handler(CallbackQueryHandler(button_callback))

    if ADMIN_CHAT_ID:
        setup_scheduler(app, int(ADMIN_CHAT_ID))

    print("🤖 Ethiopian Student Speedrun Bot is running publicly... 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
