from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# States
ASK_MHR, ASK_RHR = range(2)

user_data_store = {}

def calculate_hrr_zones(mhr, rhr):
    def hrr_range(low_pct, high_pct):
        return (
            round((mhr - rhr) * low_pct + rhr),
            round((mhr - rhr) * high_pct + rhr)
        )

    return {
        'Zone 1 (Very Light)': hrr_range(0.50, 0.60),
        'Zone 2 (Light)': hrr_range(0.60, 0.70),
        'Zone 3 (Moderate)': hrr_range(0.70, 0.80),
        'Zone 4 (Hard)': hrr_range(0.80, 0.90),
        'Zone 5 (Maximum)': hrr_range(0.90, 1.00),
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("👋 Welcome! Let's calculate your heart rate zones.\n\nPlease enter your Max Heart Rate (MHR) in BPM:")
    return ASK_MHR

async def get_mhr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        mhr = int(update.message.text)
        context.user_data["mhr"] = mhr
        await update.message.reply_text("👍 Now enter your Resting Heart Rate (RHR) in BPM:")
        return ASK_RHR
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number for MHR.")
        return ASK_MHR

async def get_rhr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        rhr = int(update.message.text)
        mhr = context.user_data["mhr"]

        zones = calculate_hrr_zones(mhr, rhr)
        message = f"✅ Here are your personalized heart rate zones (HRR-based):\n\n"
        for zone, (low, high) in zones.items():
            message += f"{zone}: {low}–{high} BPM\n"

        await update.message.reply_text(message)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number for RHR.")
        return ASK_RHR

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❎ Conversation cancelled.")
    return ConversationHandler.END

def main():
    # Replace with your own bot token
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
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
