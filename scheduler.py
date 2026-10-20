# scheduler.py
# Background checker for regular progress pings

from telegram.ext import Application

async def regular_progress_reminder(context):
    job = context.job
    chat_id = job.chat_id
    reminder_msg = (
        "⏰ **Daily Speedrun Check-In!** 🚀\n\n"
        "Yo Sid, how’s the morning study block going? Grab some water 💧, "
        "stay hydrated 🍔, and check your targets using /week1!"
    )
    await context.bot.send_message(chat_id=chat_id, text=reminder_msg)

def setup_scheduler(application: Application, chat_id: int):
    if application.job_queue and chat_id:
        application.job_queue.run_repeating(
            regular_progress_reminder, 
            interval=86400, 
            first=10, 
            chat_id=chat_id, 
            name="daily_reminder"
        )