import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from database import init_db
from handler import handle

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = os.environ["TELEGRAM_TOKEN"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hola! Soy tu bot de gastos.\n\n"
        "*Registrar un gasto:*\n"
        "• `5000 oxxo`\n"
        "• `10000 falabella débito`\n"
        "• `23000 mcdonalds, tomás y flo` _(split)_\n"
        "• `15000 doctor, mamá` _(adelanto)_\n\n"
        "*Consultas:*\n"
        "• `¿cuánto gasté este mes?`\n"
        "• `¿cuánto me deben?`\n"
        "• `flo me pagó 5000`\n"
        "• `últimos gastos`\n"
        "• `métricas`\n"
        "• `compara meses`",
        parse_mode="Markdown",
    )


async def mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text
    await update.message.chat.send_action("typing")
    respuesta = await handle(texto, user_id)
    await update.message.reply_text(respuesta, parse_mode="Markdown")


def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje))
    print("✅ Bot corriendo...")
    app.run_polling()


if __name__ == "__main__":
    main()
