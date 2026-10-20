# cloud_backup.py
import json
import os
import datetime
import asyncio
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from config import BACKUP_CHAT_ID
from database import DB_FILE

async def restore_from_telegram(bot, chat_id):
    # Safe fallback: returns False on first run if no complex file_id logic is present
    return False

async def backup_to_telegram(bot, chat_id):
    if not chat_id:
        return False
    try:
        # Ensure DB file exists
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w", encoding="utf-8") as fh:
                json.dump({"users": {}}, fh)
                
        # Read the file as plain text/JSON
        with open(DB_FILE, "r", encoding="utf-8") as fh:
            file_content = fh.read()
            
        caption = (
            f"🗄️ **Speedrun DB Backup**\n"
            f"📅 {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
            f"📝 Click to view as text!"
        )
        
        # ✅ FIX: Use InputFile to properly wrap the bytes and filename for the API
        await bot.send_document(
            chat_id=chat_id,
            document=InputFile(file_content.encode("utf-8"), filename="speedrun_progress.json"),
            caption=caption,
            parse_mode="Markdown"
        )
        return True
    except Exception as e:
        print(f"⚠️ Backup to Telegram failed: {e}")
        return False

async def backup_loop(bot, chat_id):
    while True:
        await asyncio.sleep(60 * 60)  # Wait exactly 1 hour
        if chat_id:
            await backup_to_telegram(bot, chat_id)

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Use context.bot, NOT update.effective_bot
    ok = await backup_to_telegram(context.bot, BACKUP_CHAT_ID)
    await update.message.reply_text(
        "🗄️ Backup saved to your Telegram vault as a readable file! ✅" if ok
        else "⚠️ Backup failed! Check that the bot is ADMIN in the channel and BACKUP_CHAT_ID is correct."
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 This chat's ID: `{update.effective_chat.id}`", parse_mode="Markdown")