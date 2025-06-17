import logging
import json
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===== CONFIGURACIÓN INICIAL =====
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Configuración de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'  # Logs se guardarán en archivo
)
logger = logging.getLogger(__name__)

# Carga la configuración de chats
try:
    with open('config_chats.json', 'r', encoding='utf-8') as f:
        CHAT_CONFIG = json.load(f)
except FileNotFoundError:
    logger.error("❌ Archivo config_chats.json no encontrado. Usando configuración vacía.")
    CHAT_CONFIG = {}

# ===== FUNCIONES PRINCIPALES =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /start"""
    await update.message.reply_text("¡Hola! Soy Sary el bot moderador. Usa /reglas para ver las normas.")

async def reglas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra las reglas del grupo"""
    reglas_texto = """
    📜 **REGLAS DEL GRUPO**:
    1. ✅ No enviar spam.
    2. ✅ No lenguaje ofensivo (palabras prohibidas: puta, cp, maricon, mmvrg, negro, etc).
    3. ✅ Solo enlaces permitidos: 
       - youtube.com
       - google.com
       - tiktok.com
       - instagram.com
    """
    await update.message.reply_text(reglas_texto)

async def moderar_mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Filtra contenido inapropiado"""
    chat_id = str(update.message.chat_id)
    config = CHAT_CONFIG.get(chat_id, {})
    
    if not config:
        return

    mensaje = update.message.text.lower() if update.message.text else ""
    user = update.message.from_user.username or update.message.from_user.first_name

    # Moderación de palabras prohibidas (nueva estructura)
    palabras_prohibidas = config.get("palabras_prohibidas_general", [])
    for palabra in palabras_prohibidas:
        if palabra.lower() in mensaje:
            await update.message.delete()
            alerta = config.get(
                "mensaje_alerta", 
                f"🚨 @{user} Palabra no permitida. Ver /reglas"
            )
            await update.message.reply_text(alerta)
            logger.info(f"Palabra prohibida detectada: '{palabra}' por {user}")
            break

    # Moderación de enlaces
    enlaces_permitidos = config.get("enlaces_permitidos", [])
    if ("http" in mensaje or "www." in mensaje) and enlaces_permitidos:
        if not any(dominio in mensaje for dominio in enlaces_permitidos):
            await update.message.delete()
            await update.message.reply_text(f"🔗 @{user} Enlace no autorizado. Ver /reglas")

async def dar_bienvenida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía mensajes de bienvenida"""
    chat_id = str(update.message.chat_id)
    config = CHAT_CONFIG.get(chat_id, {})
    
    if config.get("dar_bienvenida", False):
        for user in update.message.new_chat_members:
            mensaje = config.get(
                "mensaje_bienvenida", 
                f"¡Bienvenido @{user.username}! 🌟 Usa /reglas."
            )
            await update.message.reply_text(mensaje)

# ===== INICIALIZACIÓN DEL BOT =====
def main():
    application = Application.builder().token(TOKEN).build()
    
    # Handlers para comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reglas", reglas))
    
    # Handlers para mensajes
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, moderar_mensajes))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, dar_bienvenida))
    
    # Inicia el bot
    logger.info("🤖 Bot iniciado correctamente")
    application.run_polling()

if __name__ == '__main__':
    main()