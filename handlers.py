# handlers.py
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from schedule_data import CURRICULUM_DATA
from database import get_user_progress, mark_unit_done, toggle_unit

# --- TYPO-PROOF helper: find a grade's data by prefix ---
def _find_grade_data(prefix):
    for key, val in CURRICULUM_DATA.items():
        if key.startswith(prefix):
            return val
    return None

def get_next_task(user_id):
    """Finds the very first incomplete topic, starting from Grade 9."""
    progress = get_user_progress(user_id)
    grades_to_check = [
        ("Grade 9", _find_grade_data("Grade 9")),
        ("Grade 10", _find_grade_data("Grade 10")),
    ]
    for grade_name, grade_data in grades_to_check:
        if not grade_data:
            continue
        for month_name, weeks in grade_data.items():
            for week_name, days in weeks.items():
                for day_name, subjects in days.items():
                    for subject, topics in subjects.items():
                        for topic in topics:
                            if not progress.get(topic, False):
                                return {
                                    "grade": grade_name,
                                    "month": month_name,
                                    "week": week_name,
                                    "day": day_name,
                                    "subject": subject,
                                    "topic": topic,
                                }
    return None

def get_grade_stats(grade_label, user_id):
    """Stats for one grade only. Accepts 'Grade 9' or 'Grade 10'."""
    progress = get_user_progress(user_id)
    stats = {}
    months = _find_grade_data(grade_label)
    if months is None:
        return stats
    for month_name, weeks in months.items():
        for week_name, days in weeks.items():
            for day_name, subjects in days.items():
                for subject, topics in subjects.items():
                    if subject not in stats:
                        stats[subject] = {"total": 0, "completed": 0}
                    for topic in topics:
                        stats[subject]["total"] += 1
                        if progress.get(topic, False):
                            stats[subject]["completed"] += 1
    return stats

async def _render_day_view(query, user_id, grade_code, month_index, week_index, day_index):
    grade_label = "Grade 9" if grade_code == "9" else "Grade 10"
    grade_data = _find_grade_data(grade_label)
    month_name = list(grade_data.keys())[month_index]
    week_name = list(grade_data[month_name].keys())[week_index]
    day_name = list(grade_data[month_name][week_name].keys())[day_index]
    subjects_in_day = grade_data[month_name][week_name][day_name]

    response = f"🗓️ **{month_name} | {week_name} | {day_name}**\nHere are the subjects & units to finish today:\n\n"
    keyboard = []
    progress = get_user_progress(user_id)
    for subject, topics in subjects_in_day.items():
        response += f"📚 **{subject}**:\n"
        for t_idx, topic in enumerate(topics):
            done = progress.get(topic, False)
            status_icon = "✅" if done else "⬜"
            short_topic = topic[:20] + "..." if len(topic) > 20 else topic
            response += f"  • {status_icon} {topic}\n"
            keyboard.append([InlineKeyboardButton(
                f"{'✅' if done else '⬜'} {short_topic}",
                callback_data=f"dt_{grade_code}_{month_index}_{week_index}_{day_index}_{t_idx}"
            )])
        response += "\n"
    keyboard.append([InlineKeyboardButton("⬅️ Back to Days", callback_data=f"w_{grade_code}_{month_index}_{week_index}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_text(text=response, reply_markup=reply_markup, parse_mode="Markdown")
    except BadRequest:
        pass

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🇪🇹 **Welcome to Ethiopian Social Science Speedrun Bot!** 🚀🔥\n\n"
        "Your ultimate companion for Grade 9 & 10 Social Science Curriculum mastery! 🌍📚\n\n"
        "📌 **Commands:**\n"
        "• /curriculum - Explore months, weeks, days & 5 subjects 🗺️\n"
        "• /what_to_study - Get smart recommendation on what to tackle next 🧠\n"
        "• /status - Check your progress counts & completion bars 📊\n"
        "• /calendar - Speedrun exam countdown & daily pace ⏳"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def curriculum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📘 Grade 9 (፱ኛ ክፍል) Social Science", callback_data="grade_9")],
        [InlineKeyboardButton("📙 Grade 10 (፲ኛ ክፍል) Social Science", callback_data="grade_10")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🗺️ **Select a Grade Level:**", reply_markup=reply_markup, parse_mode="Markdown")

async def what_to_study_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    next_task = get_next_task(user_id)

    if not next_task:
        await update.message.reply_text(
            "🎉 **Congratulations!** You have completed the entire curriculum! 🚀",
            parse_mode="Markdown"
        )
        return

    mission_text = (
        f"🎯 **Daily Speedrun Mission**\n\n"
        f"👉 **Next Topic:**\n"
        f"📚 *{next_task['subject']}*\n"
        f"📝 {next_task['topic']}\n\n"
        f"📍 **Location:**\n"
        f"{next_task['month']} > {next_task['week']}\n"
        f"📅 {next_task['day']}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 **Current Focus:**\n"
        f"Grade: **{next_task['grade']}**\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"Stay hydrated 💧 and keep pushing! 🔥"
    )

    keyboard = [
        [InlineKeyboardButton("✅ I finished this!", callback_data="finish_daily_task")],
        [InlineKeyboardButton("🗺️ Show Full Schedule", callback_data="main_grades")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mission_text, reply_markup=reply_markup, parse_mode="Markdown")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📘 Grade 9 (፱ኛ ክፍል) Status", callback_data="status_grade_9")],
        [InlineKeyboardButton("📙 Grade 10 (፲ኛ ክፍል) Status", callback_data="status_grade_10")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📊 **Select a Grade to View Progress Dashboard:**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_date = datetime(2027, 6, 30)
    today = datetime.now()
    days_left = (target_date - today).days
    calendar_text = (
        f"🗓️ **Exam Countdown & Calendar:**\n\n"
        f"📅 Today: `{today.strftime('%b %d, %Y')}`\n"
        f"🎯 Target: `June 30, 2027`\n"
        f"⏳ **Days Left:** `{days_left} days`\n\n"
        f"Stay hydrated 💧 and follow your weekly schedule! 🚀🔥"
    )
    await update.message.reply_text(calendar_text, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    try:
        await query.answer()
    except BadRequest:
        pass
        
    data = query.data

    # --- "I finished this" from /what_to_study ---
    if data == "finish_daily_task":
        next_task = get_next_task(user_id)
        if next_task:
            mark_unit_done(user_id, next_task["topic"])
            try:
                await query.edit_message_text(
                    f"✅ **Awesome!** Marked as done:\n\n*{next_task['topic']}*\n\n"
                    f"Run /what_to_study again for the next mission! 🚀",
                    parse_mode="Markdown"
                )
            except BadRequest:
                pass
        else:
            try:
                await query.edit_message_text("🎉 You're all caught up!", parse_mode="Markdown")
            except BadRequest:
                pass
        return

    # --- Status grade selection ---
    if data == "status_main":
        keyboard = [
            [InlineKeyboardButton("📘 Grade 9 (፱ኛ ክፍል) Status", callback_data="status_grade_9")],
            [InlineKeyboardButton("📙 Grade 10 (፲ኛ ክፍል) Status", callback_data="status_grade_10")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(
                "📊 **Select a Grade to View Progress Dashboard:**",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except BadRequest:
            pass
        return

    if data in ("status_grade_9", "status_grade_10"):
        grade_label = "Grade 9" if data == "status_grade_9" else "Grade 10"
        display_name = "Grade 9 (፱ኛ ክፍል)" if grade_label == "Grade 9" else "Grade 10 (፲ኛ ክፍል)"

        stats = get_grade_stats(grade_label, user_id)
        total_all = sum(d["total"] for d in stats.values())
        done_all = sum(d["completed"] for d in stats.values())
        overall_percent = int((done_all / total_all) * 100) if total_all > 0 else 0

        blocks = 20
        filled = int((overall_percent / 100) * blocks)
        bar = "🟩" * filled + "⬜" * (blocks - filled)

        response = (
            f"📊 **{display_name} Dashboard**\n\n"
            f"🏆 **Overall Progress:**\n"
            f"{bar} `{overall_percent}%`\n"
            f"🔹 **{done_all}** / **{total_all}** topics crushed!\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📚 **Subject Breakdown:**\n"
        )
        sorted_subjects = sorted(
            stats.items(),
            key=lambda x: (x[1]["completed"] / x[1]["total"]) if x[1]["total"] > 0 else 0
        )
        for subject, sdata in sorted_subjects:
            completed = sdata["completed"]
            total = sdata["total"]
            percent = int((completed / total) * 100) if total > 0 else 0
            subj_filled = int((percent / 100) * 10)
            subj_bar = "🟩" * subj_filled + "⬜" * (10 - subj_filled)
            response += f"• **{subject}**: `{percent}%` ({completed}/{total})\n{subj_bar}\n"

        response += "\nKeep grinding, bro! 💻💧"
        keyboard = [[InlineKeyboardButton("⬅️ Back to Grade Selection", callback_data="status_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(response, reply_markup=reply_markup, parse_mode="Markdown")
        except BadRequest:
            pass
        return

    # --- Curriculum navigation ---
    if data == "main_grades":
        keyboard = [
            [InlineKeyboardButton("📘 Grade 9 (፱ኛ ክፍል) Social Science", callback_data="grade_9")],
            [InlineKeyboardButton("📙 Grade 10 (፲ኛ ክፍል) Social Science", callback_data="grade_10")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text("🗺️ **Select a Grade Level:**", reply_markup=reply_markup, parse_mode="Markdown")
        except BadRequest:
            pass
        return

    if data in ("grade_9", "grade_10"):
        grade_label = "Grade 9" if data == "grade_9" else "Grade 10"
        grade_data = _find_grade_data(grade_label)
        keyboard = []
        for index, month_name in enumerate(grade_data.keys()):
            keyboard.append([InlineKeyboardButton(f"🗓️ {month_name}", callback_data=f"m_{grade_key_code(data)}_{index}")])
        keyboard.append([InlineKeyboardButton("⬅️ Back to Grades", callback_data="main_grades")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(
                text=f"🗺️ **{grade_label}** - Choose Amharic Month:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except BadRequest:
            pass
        return

    if data.startswith("m_"):
        parts = data.split("_")
        grade_code = parts[1]
        month_index = int(parts[2])
        grade_label = "Grade 9" if grade_code == "9" else "Grade 10"
        grade_data = _find_grade_data(grade_label)
        month_name = list(grade_data.keys())[month_index]
        weeks_data = grade_data[month_name]

        keyboard = []
        for w_index, week_name in enumerate(weeks_data.keys()):
            keyboard.append([InlineKeyboardButton(f"📅 {week_name}", callback_data=f"w_{grade_code}_{month_index}_{w_index}")])
        keyboard.append([InlineKeyboardButton("⬅️ Back to Months", callback_data=f"grade_{grade_code}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(
                text=f"🗺️ **{grade_label} | {month_name}**\nSelect a Week:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except BadRequest:
            pass
        return

    if data.startswith("w_"):
        parts = data.split("_")
        grade_code = parts[1]
        month_index = int(parts[2])
        week_index = int(parts[3])
        grade_label = "Grade 9" if grade_code == "9" else "Grade 10"
        grade_data = _find_grade_data(grade_label)
        month_name = list(grade_data.keys())[month_index]
        week_name = list(grade_data[month_name].keys())[week_index]
        days_dict = grade_data[month_name][week_name]

        keyboard = []
        for d_index, day_name in enumerate(days_dict.keys()):
            keyboard.append([InlineKeyboardButton(f"📌 {day_name}", callback_data=f"d_{grade_code}_{month_index}_{week_index}_{d_index}")])
        keyboard.append([InlineKeyboardButton("⬅️ Back to Weeks", callback_data=f"m_{grade_code}_{month_index}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(
                text=f"🗺️ **{month_name} | {week_name}**\nSelect a Day to view subjects & units:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except BadRequest:
            pass
        return

    if data.startswith("d_"):
        parts = data.split("_")
        grade_code = parts[1]
        month_index = int(parts[2])
        week_index = int(parts[3])
        day_index = int(parts[4])
        await _render_day_view(query, user_id, grade_code, month_index, week_index, day_index)
        return

    if data.startswith("dt_"):
        parts = data.split("_")
        grade_code = parts[1]
        month_index = int(parts[2])
        week_index = int(parts[3])
        day_index = int(parts[4])
        t_idx = int(parts[5])
        grade_label = "Grade 9" if grade_code == "9" else "Grade 10"
        grade_data = _find_grade_data(grade_label)
        month_name = list(grade_data.keys())[month_index]
        week_name = list(grade_data[month_name].keys())[week_index]
        day_name = list(grade_data[month_name][week_name].keys())[day_index]
        subjects_dict = grade_data[month_name][week_name][day_name]

        target_topic = None
        curr_idx = 0
        for subject, topics in subjects_dict.items():
            if t_idx < curr_idx + len(topics):
                target_topic = topics[t_idx - curr_idx]
                break
            curr_idx += len(topics)

        if target_topic:
            toggle_unit(user_id, target_topic)
            await _render_day_view(query, user_id, grade_code, month_index, week_index, day_index)
        return

def grade_key_code(data: str) -> str:
    return "9" if data == "grade_9" else "10"