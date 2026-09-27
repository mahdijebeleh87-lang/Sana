import os
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ------------------------------------------------------------------
# تنظیمات: توکن‌ها رو از متغیرهای محیطی (Environment Variables) می‌خونیم
# نه اینکه مستقیم توی کد بنویسیم (امن‌تره)
# ------------------------------------------------------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
OPENAI_MODEL = "gpt-4o-mini"  # مدل ارزون و سریع، برای یه ربات چت کاملاً کافیه

# حافظه‌ی مکالمه برای هر کاربر (ساده، در حافظه‌ی برنامه نگه داشته میشه)
# چون در حافظه (RAM) هست، اگر ربات ری‌استارت بشه، حافظه پاک میشه.
user_histories = {}

MAX_HISTORY_MESSAGES = 20  # حداکثر تعداد پیام‌هایی که از هر کاربر نگه می‌داریم


def ask_ai(user_id: int, user_text: str) -> str:
    history = user_histories.setdefault(user_id, [])
    history.append({"role": "user", "content": user_text})

    # طول تاریخچه رو محدود نگه دار
    if len(history) > MAX_HISTORY_MESSAGES:
        history[:] = history[-MAX_HISTORY_MESSAGES:]

    messages = [
        {"role": "system", "content": "شما یک دستیار هوش مصنوعی مفید و دوستانه هستید که به فارسی پاسخ می‌دهد."}
    ] + history

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
    )
    reply_text = response.choices[0].message.content

    history.append({"role": "assistant", "content": reply_text})
    return reply_text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_histories[user_id] = []
    await update.message.reply_text(
        "سلام! من یه ربات هوش مصنوعی هستم و مکالمه‌مون رو به خاطر می‌سپارم.\n"
        "هر وقت خواستی حافظه‌مون پاک بشه، دستور /reset رو بفرست."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_histories[user_id] = []
    await update.message.reply_text("حافظه‌ی مکالمه پاک شد. از اول شروع می‌کنیم!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    text = update.message.text

    try:
        await context.bot.send_chat_action(chat_id=user_id, action="typing")
        reply_text = ask_ai(user_id, text)
        await update.message.reply_text(reply_text)
    except Exception as e:
        await update.message.reply_text(f"یه خطا پیش اومد، دوباره امتحان کن.\nجزئیات: {e}")


def main():
    if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
        raise RuntimeError(
            "لطفاً TELEGRAM_TOKEN و OPENAI_API_KEY رو به عنوان Environment Variable تنظیم کن."
        )

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("ربات روشن شد و در حال اجراست...")
    app.run_polling()


if __name__ == "__main__":
    main()
