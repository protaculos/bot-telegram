from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.error import BadRequest
import os

# ---------------- CONFIGURAÇÕES ----------------
TOKEN = "8559984202:AAHj4vYFkeoaFo0qmy2xaaIQCJYpwnLioqA"  # Substitua pelo seu token
SUPPORT_LINK = "https://t.me/orgia_ia"
ANIMATION_FILE_ID = "CgACAgEAAyEFAATHIl_bAAMIaWUyS17Eam4C2AABKERvS_KlEy3NAAIQCQACj9EpR4FdIDt-QU8EOAQ"

# ---------------- TEXTOS ----------------
TEXT_START = """🎉 Bem-vindo ao SinSynth! 🎉
🔥 Transforme suas fotos em vídeos incríveis com IA!
💰 Seu saldo: 1 crédito
⭐️ 1 crédito = 1 vídeo
"""

TEXT_SEND_MEDIA = """📌 Envie sua foto em boa resolução.
❌ Não envie fotos ou vídeos infantis.
"""

# ---------------- KEYBOARDS ----------------
def start_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Enviar Foto", callback_data="send_photo")],
        [InlineKeyboardButton("Progresso", callback_data="progress"),
         InlineKeyboardButton("Créditos", callback_data="credits")],
        [InlineKeyboardButton("Dúvida / Suporte", url=SUPPORT_LINK)]
    ])

def scene_kb():
    keyboard = [[InlineKeyboardButton(f"Cena {i}", callback_data=f"scene_{i}")] for i in range(1,25)]
    keyboard.append([
        InlineKeyboardButton("🏠 Início", callback_data="back_start"),
        InlineKeyboardButton("Suporte", url=SUPPORT_LINK)
    ])
    return InlineKeyboardMarkup(keyboard)

def kb_scene_action():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Cancelar", callback_data="scene_cancel")],
        [InlineKeyboardButton("Dúvida / Suporte", url=SUPPORT_LINK)]
    ])

def kb_after_confirm():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Atualizar Progresso", callback_data="progress_view")],
        [InlineKeyboardButton("🏠 Voltar ao Início", callback_data="back_start")],
        [InlineKeyboardButton("Dúvida / Suporte", url=SUPPORT_LINK)]
    ])

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sent_msg = await update.message.reply_text(TEXT_START, reply_markup=start_kb())
    if "message_history" not in context.chat_data:
        context.chat_data["message_history"] = []
    context.chat_data["message_history"].append(sent_msg.message_id)
    context.chat_data["awaiting_media"] = False

# ---------------- CALLBACK HANDLER ----------------
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    msg = q.message

    if "message_history" not in context.chat_data:
        context.chat_data["message_history"] = []

    async def safe_edit(text, keyboard):
        try:
            await msg.edit_text(text, reply_markup=keyboard)
            context.chat_data["message_history"].append(msg.message_id)
        except BadRequest:
            try:
                await msg.edit_reply_markup(reply_markup=keyboard)
            except BadRequest:
                pass

    # -------- BOTÃO "ENVIAR FOTO" --------
    if data == "send_photo":
        await safe_edit(TEXT_SEND_MEDIA, InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Início", callback_data="back_start")],
            [InlineKeyboardButton("Suporte", url=SUPPORT_LINK)]
        ]))
        context.chat_data["awaiting_media"] = True

    # -------- CENA SELECIONADA → ENVIAR GIF --------
    elif data.startswith("scene_") and data not in ["scene_confirm", "scene_cancel"]:
        scene = data.replace("scene_","")
        context.chat_data["scene"] = scene
        # Deleta GIF anterior se existir
        gif_id = context.chat_data.get("gif_message_id")
        if gif_id:
            try:
                await context.bot.delete_message(chat_id=msg.chat_id, message_id=gif_id)
            except BadRequest:
                pass

        sent_msg = await context.bot.send_animation(
            chat_id=msg.chat_id,
            animation=ANIMATION_FILE_ID,
            caption=f'🎬 Seu vídeo será criado na Cena {scene}.',
            reply_markup=kb_scene_action()
        )
        context.chat_data["gif_message_id"] = sent_msg.message_id
        context.chat_data["message_history"].append(sent_msg.message_id)

    # -------- CANCELAR GIF --------
    elif data == "scene_cancel":
        gif_id = context.chat_data.get("gif_message_id")
        if gif_id:
            try:
                await context.bot.delete_message(chat_id=msg.chat_id, message_id=gif_id)
            except BadRequest:
                pass
            context.chat_data.pop("gif_message_id", None)

    # -------- CONFIRMAR → DELETA GIF E HISTÓRICO --------
    elif data == "scene_confirm":
        gif_id = context.chat_data.get("gif_message_id")
        if gif_id:
            try:
                await context.bot.delete_message(chat_id=msg.chat_id, message_id=gif_id)
            except BadRequest:
                pass
            context.chat_data.pop("gif_message_id", None)

        # Deleta todo histórico de mensagens
        for message_id in context.chat_data.get("message_history", []):
            try:
                await context.bot.delete_message(chat_id=msg.chat_id, message_id=message_id)
            except BadRequest:
                pass
        context.chat_data["message_history"] = []

        # Confirmação
        sent_msg = await context.bot.send_message(
            chat_id=msg.chat_id,
            text="🎬 Seu vídeo foi adicionado na fila de espera, você será notificado quando estiver pronto.\n\n💰 Você consumiu 1 crédito.",
            reply_markup=kb_after_confirm()
        )
        context.chat_data["message_history"].append(sent_msg.message_id)

    # -------- VOLTAR AO INÍCIO --------
    elif data == "back_start":
        # Deleta todas as mensagens
        for message_id in context.chat_data.get("message_history", []):
            try:
                await context.bot.delete_message(chat_id=msg.chat_id, message_id=message_id)
            except:
                pass
        context.chat_data["message_history"] = []
        # Envia mensagem de início
        sent_msg = await context.bot.send_message(chat_id=msg.chat_id, text=TEXT_START, reply_markup=start_kb())
        context.chat_data["message_history"].append(sent_msg.message_id)
        context.chat_data["awaiting_media"] = False

    # -------- PROGRESSO/CRÉDITOS --------
    elif data in ["progress", "progress_view"]:
        await safe_edit("🎬 Seu vídeo está na fila de espera.", kb_after_confirm())
    elif data == "credits":
        text_credits = """💎 Comprar Créditos
1 crédito = 1 vídeo
📊 Seu saldo atual:
• Créditos grátis: 1
• Créditos pagos: 0
• Total: 1 créditos
🎯 Benefícios dos créditos pagos:
💎 Vídeo HD e sem censura!
⚡ Processamento prioritário: Pule na fila!
⚡ Acesso total: Libere a criação de todos os vídeos!
"""
        keyboard_credits = InlineKeyboardMarkup([
            [InlineKeyboardButton("1 crédito – R$19,90", callback_data="buy_1")],
            [InlineKeyboardButton("3 créditos – R$53,70", callback_data="buy_3")],
            [InlineKeyboardButton("5 créditos – R$79,50", callback_data="buy_5")],
            [InlineKeyboardButton("10 créditos – R$129,00", callback_data="buy_10")],
            [InlineKeyboardButton("Suporte", url=SUPPORT_LINK),
             InlineKeyboardButton("🏠 Início", callback_data="back_start")]
        ])
        await safe_edit(text_credits, keyboard_credits)

# ---------------- RECEBIMENTO DE FOTO ----------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    # Inicializa o histórico do chat se não existir
    if "message_history" not in context.chat_data:
        context.chat_data["message_history"] = []

    # Deleta todo histórico de mensagens já enviadas pelo bot ou pelo usuário
    for msg_id in context.chat_data["message_history"]:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except BadRequest:
            pass
    context.chat_data["message_history"] = []

    # Salva a nova foto
    if update.message.photo:
        file_obj = await update.message.photo[-1].get_file()
        os.makedirs("downloads", exist_ok=True)
        file_path = f"downloads/{user_id}_photo.jpg"
        await file_obj.download_to_drive(file_path)
        context.chat_data["user_photo"] = file_path

        # Adiciona a foto enviada ao histórico
        context.chat_data["message_history"].append(update.message.message_id)

        # Envia diretamente o menu de cenas
        sent_msg = await update.message.reply_text(
            "✅ Foto recebida!\nEscolha a cena do vídeo:",
            reply_markup=scene_kb()
        )
        context.chat_data["message_history"].append(sent_msg.message_id)

    else:
        sent_msg = await update.message.reply_text("❌ Por favor, envie apenas uma foto.")
        context.chat_data["message_history"].append(sent_msg.message_id)

# ---------------- MAIN ----------------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handler))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

print("BOT RODANDO...")
app.run_polling()
