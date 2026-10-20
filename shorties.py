# shorties.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Map grades to their subjects and folder names
GRADE_DATA = {
    "grade_9": {
        "name": "Grade 9",
        "base_folder": "G9",
        "subjects": {
            "Mathematics": "mat",
            "History": "his",
            "Geography": "geo",
            "Economics": "eco",
            "Civics": "cit"
        }
    },
    "grade_11": {
        "name": "Grade 11",
        "base_folder": "G11",
        "subjects": {
            "Economics": "eco",
            "Geography": "geo",
            "History": "his"
        }
    }
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

async def shorties_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📘 Grade 9 Shorties", callback_data="shorties_grade_9")],
        [InlineKeyboardButton("📙 Grade 11 Shorties", callback_data="shorties_grade_11")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤫 **Secret Vault: Shorties**\n\n"
        "Quick revision notes. Select your grade to access the vault:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def shorties_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # 1. Grade Selection -> Show Subjects
    if data in ["shorties_grade_9", "shorties_grade_11"]:
        grade_key = "grade_9" if data == "shorties_grade_9" else "grade_11"
        grade_info = GRADE_DATA[grade_key]
        
        keyboard = []
        for subject in grade_info["subjects"].keys():
            keyboard.append([InlineKeyboardButton(f"📚 {subject}", callback_data=f"shorties_subj_{grade_key}_{subject.lower()}")])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="shorties_back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"📚 **Select a Subject for {grade_info['name']}:**", 
            reply_markup=reply_markup, 
            parse_mode="Markdown"
        )

    # 2. Subject Selection -> Show Units (files in folder)
    elif data.startswith("shorties_subj_"):
        # ✅ SAFE EXTRACTION: Avoids .split("_") breaking "grade_9"
        remainder = data[len("shorties_subj_"):]
        
        if remainder.startswith("grade_9_"):
            grade_key = "grade_9"
            subject_key = remainder[len("grade_9_"):]
        elif remainder.startswith("grade_11_"):
            grade_key = "grade_11"
            subject_key = remainder[len("grade_11_"):]
        else:
            await query.edit_message_text("⚠️ Invalid data format.")
            return
            
        grade_info = GRADE_DATA[grade_key]
        subject_name = next((k for k, v in grade_info["subjects"].items() if k.lower() == subject_key), None)
        folder_name = grade_info["subjects"].get(subject_name)
        base_folder = grade_info["base_folder"]

        if not folder_name or not subject_name:
            await query.edit_message_text("⚠️ Subject folder mapping missing.")
            return

        folder_path = os.path.join(BASE_DIR, base_folder, folder_name)
        
        if not os.path.exists(folder_path):
            await query.edit_message_text(
                f"⚠️ The folder `{base_folder}/{folder_name}` is missing in your bot directory!\n\n"
                f"Please create it and add `.txt` files inside.",
                parse_mode="Markdown"
            )
            return

        # Dynamically find all .txt files
        files = sorted([f for f in os.listdir(folder_path) if f.endswith('.txt')])
        if not files:
            await query.edit_message_text(
                f"📂 The `{base_folder}/{folder_name}` folder is empty!\n\n"
                f"Please add `.txt` files (like `u1.txt`) inside it.",
                parse_mode="Markdown"
            )
            return

        keyboard = []
        for f in files:
            unit_name = f.replace('.txt', '').upper()
            callback_data = f"shorties_file_{grade_key}_{subject_key}_{f}"
            keyboard.append([InlineKeyboardButton(f"📄 {unit_name}", callback_data=callback_data)])

        grade_num = grade_key.split("_")[1]
        keyboard.append([InlineKeyboardButton(f"⬅️ Back to {grade_info['name']} Subjects", callback_data=f"shorties_grade_{grade_num}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"📂 **{grade_info['name']} - {subject_name} Notes**\nSelect a unit to read:", reply_markup=reply_markup, parse_mode="Markdown")

    # 3. Unit Selection -> Read and Display the Note
    elif data.startswith("shorties_file_"):
        prefix_len = len("shorties_file_")
        remainder = data[prefix_len:]
        
        # ✅ SAFE EXTRACTION for file reading
        if remainder.startswith("grade_9_"):
            grade_key = "grade_9"
            rest = remainder[len("grade_9_"):]
        elif remainder.startswith("grade_11_"):
            grade_key = "grade_11"
            rest = remainder[len("grade_11_"):]
        else:
            await query.edit_message_text("⚠️ Invalid data format.")
            return
            
        subject_key, filename = rest.split("_", 1) # Split only on the FIRST underscore
        
        grade_info = GRADE_DATA[grade_key]
        subject_name = next((k for k, v in grade_info["subjects"].items() if k.lower() == subject_key), None)
        folder_name = grade_info["subjects"].get(subject_name)
        base_folder = grade_info["base_folder"]
        file_path = os.path.join(BASE_DIR, base_folder, folder_name, filename)

        if os.path.exists(file_path):
            unit_display = filename.replace('.txt', '').upper()
            
            # Always send as file for better study experience
            await query.answer("📥 Sending note...", show_alert=False)
            with open(file_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=file,
                    filename=filename,
                    caption=f"📄 **{grade_info['name']} - {subject_name}**\n**{unit_display}**\n\n",
                    parse_mode="Markdown"
                )
        else:
            await query.edit_message_text("⚠️ File not found.")

    # 4. Back buttons
    elif data == "shorties_back":
        keyboard = [
            [InlineKeyboardButton("📘 Grade 9 Shorties", callback_data="shorties_grade_9")],
            [InlineKeyboardButton("📙 Grade 11 Shorties", callback_data="shorties_grade_11")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🤫 **Secret Vault: Shorties**\n\nSelect your grade:", reply_markup=reply_markup, parse_mode="Markdown")
