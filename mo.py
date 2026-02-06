import google.generativeai as genai
import telegram
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext,
)
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update

# تنظیمات
GOOGLE_API_KEY = ""
TELEGRAM_BOT_TOKEN = ":"  # توکن ربات تلگرام خود را اینجا قرار دهید

# مراحل گفتگو
(
    GETTING_GRADE,
    GETTING_SUBJECT,
    GETTING_ISSUE,
    GETTING_ADDITIONAL_INFO,
    TYPING_REPLY,
) = range(5)

# پیکربندی Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# پیکربندی ربات تلگرام
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()


# تعریف handler ها
async def start(update: Update, context: CallbackContext) -> int:
    """شروع گفتگو و پرسیدن مقطع تحصیلی"""
    await update.message.reply_text(
        "سلام! من معلم‌یار هستم. برای ارائه مشاوره بهتر، لطفا ابتدا مقطع تحصیلی خود را وارد کنید:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return GETTING_GRADE


async def getting_grade(update: Update, context: CallbackContext) -> int:
    """ذخیره مقطع تحصیلی و پرسیدن درس"""
    context.user_data["grade"] = update.message.text
    reply_keyboard = [
        ["ابتدایی", "متوسطه اول"],
        ["متوسطه دوم", "فنی و حرفه‌ای"],
        ["دانشگاه", "سایر"],
    ]  # می توانید لیست مقاطع را تکمیل تر کنید
    await update.message.reply_text(
        "چه درسی تدریس می‌کنید؟",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="درس؟"
        ),
    )
    return GETTING_SUBJECT


async def getting_subject(update: Update, context: CallbackContext) -> int:
    """ذخیره درس و پرسیدن مشکل"""
    context.user_data["subject"] = update.message.text
    await update.message.reply_text(
        "در چه زمینه‌ای نیاز به راهنمایی دارید؟ (طرح درس، روش تدریس، مدیریت کلاس، ارزشیابی، تولید محتوا و ...)"
    )
    return GETTING_ISSUE


async def getting_issue(update: Update, context: CallbackContext) -> int:
    """ذخیره مشکل و پرسیدن اطلاعات تکمیلی"""
    context.user_data["issue"] = update.message.text
    await update.message.reply_text(
        "لطفا اطلاعات تکمیلی مانند سابقه تدریس، سبک تدریس، چالش‌های خاص کلاس و ... را در صورت امکان شرح دهید:"
    )
    return GETTING_ADDITIONAL_INFO


async def restart(update: Update, context: CallbackContext) -> int:
    """پاک کردن اطلاعات کاربر و شروع مجدد مکالمه از مرحله پرسیدن مقطع تحصیلی"""
    context.user_data.clear()  # پاک کردن تمام اطلاعات کاربر
    await update.message.reply_text(
        "اطلاعات شما پاک شد. برای شروع دوباره لطفا مقطع تحصیلی خود را وارد کنید:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return GETTING_GRADE  # بازگشت به مرحله اول (پرسیدن مقطع تحصیلی)


async def getting_additional_info(update: Update, context: CallbackContext) -> int:
    """ذخیره اطلاعات تکمیلی و نمایش پیام اولیه برای شروع پرسش و پاسخ"""
    context.user_data["additional_info"] = update.message.text
    await update.message.reply_text(
        "خیلی ممنون. حالا می‌توانید سوالات تکمیلی خود را بپرسید یا اطلاعات بیشتری ارائه دهید."
    )
    return TYPING_REPLY


async def handle_message(update: Update, context: CallbackContext) -> int:
    """پردازش پیام کاربر، ارسال پاسخ Gemini و نمایش پیام راهنمای شروع مجدد"""
    user_message = update.message.text
    state = context.user_data
    try:
        # ساخت prompt با اطلاعات جمع‌آوری شده
        prompt = f"""
        شما یک ربات تخصصی هوش مصنوعی به نام "معلم‌یار" هستید که به معلمان ایرانی مشاوره می‌دهید.
        لطفا به سوال معلمی زیر با دقت و به زبان فارسی پاسخ دهید.

        کاربر: {user_message}
        مقطع تحصیلی: {state.get("grade", "نامشخص")}
        درس: {state.get("subject", "نامشخص")}
        موضوع: {state.get("issue", "نامشخص")}
        اطلاعات تکمیلی: {state.get("additional_info", "نامشخص")}

        لطفا با لحنی حرفه‌ای و دلسوزانه پاسخ دهید و در صورت نیاز اطلاعات تکمیلی از کاربر درخواست کنید.
        به یاد داشته باشید که شما به معلمان ایرانی مشاوره می‌دهید، پس شرایط اموزشی، اقتصادی و فرهنگی ایران را در نظر بگیرید.
        """
        response = model.generate_content(prompt)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=response.text
        )

        # نمایش پیام راهنمای شروع مجدد
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="برای شروع مجدد و ورود اطلاعات جدید، /restart را بزنید.",
        )

    except Exception as e:
        print(f"Error: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="متاسفم، مشکلی پیش اومد. لطفا دوباره امتحان کنید.",
        )
    return TYPING_REPLY


async def cancel(update: Update, context: CallbackContext) -> int:
    """لغو و پایان گفتگو"""
    user = update.message.from_user
    await update.message.reply_text(
        "گفتگو لغو شد. برای شروع دوباره /start را بزنید.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        GETTING_GRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, getting_grade)],
        GETTING_SUBJECT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, getting_subject)
        ],
        GETTING_ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, getting_issue)],
        GETTING_ADDITIONAL_INFO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, getting_additional_info)
        ],
        TYPING_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CommandHandler("restart", restart),  # اضافه کردن restart به fallbacks
    ],
)

application.add_handler(conv_handler)
application.add_handler(CommandHandler("restart", restart))  # اضافه کردن handler برای دستور restart

# شروع ربات
application.run_polling()