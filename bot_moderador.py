import logging
import json
import os
import re  # Nuevo módulo para expresiones regulares
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
    filename='bot.log'
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
    2. ✅ No lenguaje ofensivo (ej: insultos, groserías, etc).
    3. ✅ Solo enlaces permitidos: 
       - youtube.com
       - google.com
       - tiktok.com
       - instagram.com
    """
    await update.message.reply_text(reglas_texto)

def generar_patron(palabra):
    """Genera un patrón regex para detectar variantes de palabras"""
    sustituciones = {
        'a': '[a@4á]',
        'e': '[e3é]',
        'i': '[i1í]',
        'o': '[o0ó]',
        'u': '[uúü]',
        ' ': r'\s*'  # Permite espacios variables
    }
    patron = ''.join([sustituciones.get(c, re.escape(c)) for c in palabra.lower()])
    return re.compile(rf'\b{patron}\b', re.IGNORECASE)

async def moderar_mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Filtra contenido inapropiado con detección avanzada"""
    chat_id = str(update.message.chat_id)
    config = CHAT_CONFIG.get(chat_id, {})
    
    if not config:
        return

    mensaje = update.message.text or ""
    user = update.message.from_user.username or update.message.from_user.first_name

    # Moderación de palabras prohibidas (sistema mejorado)
    palabras_prohibidas = config.get("palabras_prohibidas_general", [])
    for palabra in palabras_prohibidas:
        patron = generar_patron(palabra)
        if patron.search(mensaje):
            await update.message.delete()
            alerta = config.get(
                "mensaje_alerta", 
                f"🚨 @{user} Contenido no permitido detectado. Ver /reglas"
            )
            await update.message.reply_text(alerta)
            logger.info(f"Detección avanzada: '{palabra}' en mensaje de {user}")
            break  # Detener después de la primera coincidencia

    # Moderación de enlaces (se mantiene igual)
    enlaces_permitidos = config.get("enlaces_permitidos", [])
    if ("http" in mensaje.lower() or "www." in mensaje.lower()) and enlaces_permitidos:
        if not any(dominio in mensaje.lower() for dominio in enlaces_permitidos):
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
    logger.info("🤖 Bot iniciado con detección avanzada")
    application.run_polling()

if __name__ == '__main__':
    main()