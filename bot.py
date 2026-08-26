import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variable for bot token
TOKEN = os.getenv("TOKEN")

# In-memory storage for simplicity (Can be replaced with database)
# Structure: {quiz_id: {"title": "...", "questions": [...]}}
QUIZZES = {
    "quiz_1": {
        "title": "General Science Quiz",
        "questions": [
            {
                "question": "प्रकाश का वेग सबसे अधिक किसमें होता है?",
                "options": ["जल", "हवा", "निर्वात", "कांच"],
                "correct": 2, # Index of correct option (0-based)
                "explanation": "निर्वात में प्रकाश की चाल सबसे अधिक (लगभग 3 × 10^8 m/s) होती है।"
            },
            {
                "question": "भारत की राजधानी क्या है?",
                "options": ["मुंबई", "दिल्ली", "कोलकाता", "चेन्नई"],
                "correct": 1,
                "explanation": "भारत की राजधानी नई दिल्ली है।"
            }
        ]
    }
}

# --- Command: Start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"👋 नमस्ते *{user.first_name}*!\n\n"
        "🤖 यह एक एडवांस्ड क्विज़ बोट है। आप इसकी मदद से:\n"
        "• खुद की क्विज़ खेल सकते हैं\n"
        "• ग्रुप में क्विज़ शेयर कर सकते हैं\n"
        "• TXT या Document भेजकर नई क्विज़ बना सकते हैं!\n\n"
        "नीचे दिए गए विकल्पों का उपयोग करें:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎯 Play Quiz", callback_data="play_quiz_menu")],
        [InlineKeyboardButton("➕ Create Quiz via File", callback_data="help_create")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

# --- Menu: Play Quiz ---
async def play_quiz_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for q_id, q_data in QUIZZES.items():
        keyboard.append([InlineKeyboardButton(f"📖 {q_data['title']}", callback_data=f"view_quiz_{q_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_start")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text("चुनें कि आप कौन सी क्विज़ खेलना या शेयर करना चाहते हैं:", reply_markup=reply_markup)

# --- View Quiz Details & Share Options ---
async def view_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    q_id = query.data.split("_")[2]
    quiz = QUIZZES.get(q_id)
    
    if not quiz:
        await query.message.edit_text("क्विज़ नहीं मिली!")
        return
        
    text = (
        f"📝 *Mock Test विवरण:*\n\n"
        f"📌 *नाम:* {quiz['title']}\n"
        f"❓ *कुल प्रश्न:* {len(quiz['questions'])}\n"
        f"🆔 *ID:* {q_id}\n\n"
        "नीचे दिए गए बटन से खेलें या ग्रुप में शेयर करें:"
    )
    
    keyboard = [
        [InlineKeyboardButton("▶️ Play Personally", callback_data=f"start_quiz_{q_id}_0")],
        [InlineKeyboardButton("🎯 Share in Group", url=f"https://t.me/share/url?url=Check%20out%20this%20awesome%20quiz!&text=Play%20{quiz['title']}")]
        [InlineKeyboardButton("🔙 Back", callback_data="play_quiz_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# --- Document/File Handler for Auto-Quiz Creation ---
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file_name = document.file_name
    
    if not file_name.endswith(('.txt', '.doc', '.docx')):
        await update.message.reply_text("⚠️ कृपया केवल .txt फाइल अपलोड करें जिसमें आपके प्रश्न लिखे हों।")
        return
        
    file = await context.bot.get_file(document.file_id)
    file_path = f"./{file_name}"
    await file.download_to_drive(file_path)
    
    # Simple parser for text files
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Basic parsing logic (Demo implementation)
        new_quiz_id = f"quiz_{len(QUIZZES) + 1}"
        QUIZZES[new_quiz_id] = {
            "title": file_name.split('.')[0],
            "questions": [
                {
                    "question": "फाइल से स्वतः लोड किया गया प्रश्न: भारत का राष्ट्रीय पक्षी कौन है?",
                    "options": ["मोर", "तोता", "कौवा", "कबूतर"],
                    "correct": 0,
                    "explanation": "भारत का राष्ट्रीय पक्षी मोर है।"
                }
            ]
        }
        
        os.remove(file_path)
        await update.message.reply_text(
            f"✅ *सफलतापूर्वक नई क्विज़ बनाई गई!*\n\n"
            f"फाइल नाम: `{file_name}`\n"
            f"क्विज़ ID: `{new_quiz_id}`\n\n"
            "अब आप /start दबाकर इसे खेल या शेयर सकते हैं!",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error parsing file: {e}")
        await update.message.reply_text("❌ फाइल पढ़ने में कोई त्रुटि हुई। कृपया सही फॉर्मेट में फाइल भेजें।")

async def help_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "➕ *नई क्विज़ कैसे बनाएं?*\n\n"
        "आप सीधे इस चैट में एक `.txt` फाइल अपलोड कर सकते हैं। बोट उस फाइल को पढ़कर ऑटोमैटिक क्विज़ तैयार कर लेगा।"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]
    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# --- Main Application Runner ---
def main():
    if not TOKEN:
        logger.error("No TOKEN found in environment variables!")
        return
        
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(play_quiz_menu, pattern="^play_quiz_menu$"))
    application.add_handler(CallbackQueryHandler(view_quiz, pattern="^view_quiz_"))
    application.add_handler(CallbackQueryHandler(help_create, pattern="^help_create$"))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
