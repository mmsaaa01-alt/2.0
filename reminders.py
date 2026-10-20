# reminders.py
from datetime import time
from telegram.ext import ContextTypes
from schedule_data import CURRICULUM_DATA
from database import load_progress

# Helper function to find the next incomplete topic
def get_next_incomplete_topic():
    progress = load_progress()
    grades_to_check = ["Grade 9 (፱ኛ ክል)", "Grade 10 (፲ኛ ክፍል)"]
    
    for grade_name in grades_to_check:
        if grade_name not in CURRICULUM_DATA:
            continue
        months = CURRICULUM_DATA[grade_name]
        for month_name, weeks in months.items():
            for week_name, days in weeks.items():
                for day_name, subjects in days.items():
                    for subject, topics in subjects.items():
                        for topic in topics:
                            if not progress.get(topic, False):
                                return subject, topic
    return None, None

# The actual function that runs at 6 PM
async def daily_6pm_reminder(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    subject, topic = get_next_incomplete_topic()
    
    if subject and topic:
        # You still have work to do!
        message = (
            f"⏰ **6 PM Daily Check-in!** ⏰\n\n"
            f"Hey! It's 6 PM and you haven't finished today's study goal yet. 📉\n\n"
            f"👉 **Your next topic is:**\n"
            f"📚 *{subject}*\n"
            f"📝 {topic}\n\n"
            f"Grab some water 💧, open your books, and get back to the grind! You got this! 💪🔥\n\n"
            f"Use /what_to_study to see your full daily mission."
        )
    else:
        # Curriculum is 100% complete!
        message = (
            f"⏰ **6 PM Daily Check-in!** ⏰\n\n"
            f"🎉 **Amazing job!** You have completed the entire curriculum! \n"
            f"Take the night off, you've earned it! 🏆🍕"
        )
        
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

# Function to register the 6 PM job
def setup_6pm_reminder(application, chat_id: int):
    if application.job_queue and chat_id:
        # time(18, 0) means 6:00 PM (24-hour format)
        application.job_queue.run_daily(
            daily_6pm_reminder,
            time=time(18, 0),
            chat_id=chat_id,
            name="daily_6pm_reminder"
        )
        print("⏰ 6 PM Daily Reminder scheduled successfully!")
