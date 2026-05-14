import os
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
MADINA_USERNAME = "Madina_iticket"

claude = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
conversation_history = {}

SYSTEM_PROMPT = """Sen iTicket.uz uchun professional yordamchi assistantsan.
Vazifang:
1. Mijozlarga bilet, joy, lokatsiya, konsert haqida savollarga javob berish
2. iticket.uz havolalarini olib, konsertlar uchun Instagram caption yozish
3. Jamoaga ma'lumot uzatish

Qoidalar:
- Har doim o'zbek tilida javob ber (agar rus tilida so'rashsa, rus tilida javob ber)
- Qisqa, aniq va do'stona bo'l
- Bilet qolmagan bo'lsa, muqobil taklif qil
- iticket.uz havolasi kelsa — darhol caption va dizaynerga brief yozib ber

iTicket haqida umumiy ma'lumot:
- Sayt: iticket.uz
- Bilet olish: sayt orqali yoki kassadan
- Muammo bo'lsa: iticket.uz support bilan bog'lanish tavsiya qilinadi"""


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    chat_id = message.chat_id
    user_id = message.from_user.id
    text = message.text
    bot_username = context.bot.username

    is_private = message.chat.type == "private"
    is_bot_mentioned = f"@{bot_username}" in text
    is_madina_mentioned = f"@{MADINA_USERNAME}" in text
    is_reply_to_bot = (
        message.reply_to_message and
        message.reply_to_message.from_user.id == context.bot.id
    )

    if not is_private and not is_bot_mentioned and not is_madina_mentioned and not is_reply_to_bot:
        return

    clean_text = text.replace(f"@{bot_username}", "").replace(f"@{MADINA_USERNAME}", "").strip()

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": clean_text
    })

    if len(conversation_history[user_id]) > 10:
        conversation_history[user_id] = conversation_history[user_id][-10:]

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        response = claude.messages.create(
            model="claude-opus-4-5",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=conversation_history[user_id]
        )

        reply = response.content[0].text

        conversation_history[user_id].append({
            "role": "assistant",
            "content": reply
        })

        await message.reply_text(reply)

    except Exception as e:
        await message.reply_text("Texnik xatolik yuz berdi. Iltimos qayta urinib ko'ring.")
        print(f"Xato: {e}")


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot ishga tushdi! ✅")
    app.run_polling()


if __name__ == "__main__":
    main()
