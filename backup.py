# backup.py
import os
import io
import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import BACKUP_CHAT_ID
from database import DB_FILE

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Check if channel ID is configured
    if not BACKUP_CHAT_ID:
        await update.message.reply_text("⚠️ Backup channel ID is not set in config.py!")
        return
        
    # 2. Check if database file exists
    if not os.path.exists(DB_FILE):
        await update.message.reply_text("⚠️ No database file found to backup!")
        return
        
    try:
        # 3. Read the database file
        with open(DB_FILE, "rb") as f:
            file_content = f.read()
            
        # 4. Create a nice caption with the date
        caption = (
            f"🗄️ **Speedrun DB Backup**\n"
            f"📅 {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
            f" Click to view as text!"
        )
        
        # 5. Send the file to the channel
        await context.bot.send_document(
            chat_id=BACKUP_CHAT_ID,
            document=io.BytesIO(file_content),
            filename="speedrun_progress.json",
            caption=caption,
            parse_mode="Markdown"
        )
        
        # 6. Notify the user
        await update.message.reply_text("✅ Backup successfully sent to the channel!")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Backup failed: {e}")