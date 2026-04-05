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
        "👋 Hola, soy tu asistente de gastos personales.\n\n"
        "*Para registrar un gasto*, escríbeme el monto y el lugar:\n"
        "— Gasto personal: `5.000 oxxo` o `10.000 falabella débito`\n"
        "— Gasto compartido: `23.000 mcdonalds con [nombre] y [nombre]`\n"
        "— Adelanto por otra persona: `15.000 doctor, [nombre]`\n\n"
        "*Para consultar*, puedes preguntarme:\n"
        "— ¿Cuánto gasté este mes?\n"
        "— ¿Cuánto me debe [nombre]?\n"
        "— Muéstrame mis últimos gastos\n"
        "— Métricas del mes\n"
        "— Compara este mes con el anterior",
        parse_mode="Markdown",
    )


async def mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ignorar mensajes sin texto (fotos, stickers, etc.)
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    texto = update.message.text
    await update.message.chat.send_action("typing")
    respuesta = await handle(texto, user_id)
    await update.message.reply_text(respuesta, parse_mode="Markdown")


def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, mensaje))
    print("✅ Bot corriendo...")
    app.run_polling()


if __name__ == "__main__":
    main()
