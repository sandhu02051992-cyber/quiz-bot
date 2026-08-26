from telegram.request import HTTPXRequest
import os
import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# यहाँ BotFather से मिला हुआ Token डालें
TOKEN = "8996053059:AAGgpAuFLjfc3cDEpXphxeKW1PBX1COUG60E"

def load_questions():
    try:
        df = pd.read_excel('quiz.xlsx')
        return df.to_dict(orient='records')
    except Exception as e:
        print("Excel file error:", e)
        return []

def generate_pdf_report(user_name, user_id, topic_name, score, total):
    pdf_filename = f"Scorecard_{user_id}.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        alignment=1,
        spaceAfter=15,
        textColor=colors.HexColor("#1A365D")
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 12
    normal_style.leading = 16
    
    elements = []
    elements.append(Paragraph("<b>Quiz Performance Certificate</b>", title_style))
    elements.append(Spacer(1, 15))
    
    percentage = round((score / total) * 100, 2)
    
    data = [
        ["Student Name / ID:", str(user_name)],
        ["Topic Name:", str(topic_name)],
        ["Score Obtained:", f"{score} / {total}"],
        ["Percentage:", f"{percentage}%"],
        ["Created By:", "DEEPAK"]
    ]
    
    t = Table(data, colWidths=[150, 250])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#EDF2F7")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0"))
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<i>Thank you for participating in the quiz! Keep learning.</i>", normal_style))
    
    doc.build(elements)
    return pdf_filename

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = load_questions()
    if not questions:
        await update.message.reply_text("❌ क्विज़ फाइल नहीं मिली या खाली है।")
        return
    
    total_q = len(questions)
    first_q = questions[0]
    topic = first_q.get('Topic', 'General Quiz')
    time_limit = first_q.get('TimeLimit', 20)
    
    # आपकी इमेज के जैसा हूबहू लेआउट
    details_text = (
        f"📝 <b>Mock Test विवरण:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 <b>नाम:</b> {topic}\n"
        f"🆓 <b>प्रकार:</b> Full Quiz\n"
        f"❓ <b>कुल प्रश्न:</b> {total_q}\n"
        f"⏱ <b>समय:</b> {time_limit}s प्रति प्रश्न\n"
        f"👨‍🏫 <b>क्रिएटर:</b> DEEPAK\n"
        f"🆔 <b>ID:</b> DPK{total_q}99\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤝 <b>Created & Directed by: DEEPAK</b>"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Play Personally", callback_data="start_quiz_now")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(details_text, reply_markup=reply_markup, parse_mode='HTML')

async def start_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    questions = load_questions()
    context.user_data['score'] = 0
    context.user_data['current_q'] = 0
    await send_question(update, context, questions)

async def send_question(update, context, questions):
    q_idx = context.user_data['current_q']
    if q_idx < len(questions):
        q = questions[q_idx]
        keyboard = [
            [InlineKeyboardButton(str(q['OptionA']), callback_data=f"ans_0_{q_idx}"),
             InlineKeyboardButton(str(q['OptionB']), callback_data=f"ans_1_{q_idx}")],
            [InlineKeyboardButton(str(q['OptionC']), callback_data=f"ans_2_{q_idx}"),
             InlineKeyboardButton(str(q['OptionD']), callback_data=f"ans_3_{q_idx}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        topic = q.get('Topic', 'General Quiz')
        time_limit = q.get('TimeLimit', 20)
        
        caption = (
            f"📚 <b>विषय: {topic}</b> | ⏱ {time_limit}s\n\n"
            f"<b>प्रश्न {q_idx + 1}: {q['Question']}</b>\n\n"
            f"🤝 <b>Created & Directed by: DEEPAK</b>"
        )
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=caption,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        score = context.user_data['score']
        total = len(questions)
        first_q = questions[0]
        topic = first_q.get('Topic', 'General Quiz')
        user = update.effective_user
        user_name = user.full_name if user else "Student"
        user_id = user.id if user else 12345
        
        msg = f"🎯 <b>क्विज़ समाप्त!</b>\n\n" \
              f"📚 <b>Topic:</b> {topic}\n" \
              f"📊 <b>आपका स्कोर:</b> {score}/{total}\n\n" \
              f"🤝 <b>Created & Directed by: DEEPAK</b>\n\n" \
              f"📄 आपकी Scorecard PDF जनरेट की जा रही है..."
        
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode='HTML')
        
        # PDF Generator Logic
        try:
            pdf_path = generate_pdf_report(user_name, user_id, topic, score, total)
            with open(pdf_path, 'rb') as pdf_file:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=pdf_file,
                    filename=f"{topic}_Scorecard.pdf",
                    caption="🏆 यह रहा आपका आधिकारिक क्विज़ रिजल्ट स्कोरकार्ड (PDF)!"
                )
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except Exception as e:
            print("PDF Error:", e)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split('_')
    user_ans = int(data_parts[1])
    q_idx = int(data_parts[2])
    
    questions = load_questions()
    q = questions[q_idx]
    
    if user_ans == int(q['Correct']):
        context.user_data['score'] += 1
        await query.message.reply_text("✅ बिल्कुल सही उत्तर!")
    else:
        explanation = q.get('Explanation', 'कोई व्याख्या उपलब्ध नहीं है।')
        await query.message.reply_text(f"❌ गलत उत्तर!\n\n💡 <b>व्याख्या:</b> {explanation}", parse_mode='HTML')
    
    context.user_data['current_q'] += 1
    await send_question(update, context, questions)

def main():
    request_kwargs = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    app = Application.builder().token(TOKEN).request(request_kwargs).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", start))
    app.add_handler(CallbackQueryHandler(start_quiz_callback, pattern="^start_quiz_now$"))
    app.add_handler(CallbackQueryHandler(handle_answer, pattern="^ans_"))

    app.run_polling()

if __name__ == '__main__':
    main()
