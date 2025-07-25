import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Conversation states
CHOOSING_METHOD, ASK_MHR, ASK_RHR = range(3)

def calculate_hrr_zones(mhr, rhr):
    def hrr_range(low_pct, high_pct):
        return (
            round((mhr - rhr) * low_pct + rhr),
            round((mhr - rhr) * high_pct + rhr),
        )
    return {
        "Zone 1 (Very Light)": hrr_range(0.50, 0.60),
        "Zone 2 (Light)": hrr_range(0.60, 0.70),
        "Zone 3 (Moderate)": hrr_range(0.70, 0.80),
        "Zone 4 (Hard)": hrr_range(0.80, 0.90),
        "Zone 5 (Maximum)": hrr_range(0.90, 1.00),
    }


def calculate_simple_zones(mhr):
    def percent_range(low_pct, high_pct):
        return (round(mhr * low_pct), round(mhr * high_pct))

    return {
        "Zone 1 (Very Light)": percent_range(0.50, 0.60),
        "Zone 2 (Light)": percent_range(0.60, 0.70),
        "Zone 3 (Moderate)": percent_range(0.70, 0.80),
        "Zone 4 (Hard)": percent_range(0.80, 0.90),
        "Zone 5 (Maximum)": percent_range(0.90, 1.00),
    }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [
            InlineKeyboardButton("I have both MHR & RHR", callback_data="both"),
            InlineKeyboardButton("I have only MHR", callback_data="mhr_only"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Welcome! Choose your input method:", reply_markup=reply_markup
    )
    return CHOOSING_METHOD


async def choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    method = query.data
    context.user_data["method"] = method

    if method == "both":
        await query.edit_message_text("Please enter your Max Heart Rate (MHR) in BPM:")
        return ASK_MHR
    else:  # mhr_only
        await query.edit_message_text("Please enter your Max Heart Rate (MHR) in BPM:")
        return ASK_MHR


async def get_mhr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        mhr = int(update.message.text)
        context.user_data["mhr"] = mhr
        method = context.user_data.get("method")

        if method == "both":
            await update.message.reply_text("👍 Now enter your Resting Heart Rate (RHR) in BPM:")
            return ASK_RHR
        else:
            zones = calculate_simple_zones(mhr)
            message = "✅ Here are your heart rate zones (based on MHR only):\n\n"
            for zone, (low, high) in zones.items():
                message += f"{zone}: {low}–{high} BPM\n"
            await update.message.reply_text(message)
            await send_restart_button(update, context)
            return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number for MHR.")
        return ASK_MHR


async def get_rhr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        rhr = int(update.message.text)
        mhr = context.user_data["mhr"]
        zones = calculate_hrr_zones(mhr, rhr)

        message = "✅ Here are your personalized heart rate zones (HRR-based):\n\n"
        for zone, (low, high) in zones.items():
            message += f"{zone}: {low}–{high} BPM\n"

        await update.message.reply_text(message)
        await send_restart_button(update, context)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number for RHR.")
        return ASK_RHR


async def send_restart_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔄 Restart", callback_data="restart")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "You can restart the process anytime:", reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "restart":
        context.user_data.clear()
        await query.edit_message_text(
            "👋 Restarting...\n\nPlease enter your Max Heart Rate (MHR) in BPM:"
        )
        return ASK_MHR


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❎ Conversation cancelled.")
    return ConversationHandler.END


def main():
    TOKEN = os.environ["BOT_TOKEN"]

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_METHOD: [
                CallbackQueryHandler(choose_method, pattern="^(both|mhr_only)$"),
                CallbackQueryHandler(button_handler, pattern="^restart$"),
            ],
            ASK_MHR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_mhr)],
            ASK_RHR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rhr)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
