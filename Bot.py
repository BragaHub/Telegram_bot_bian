import os
import uuid
import sqlite3
import requests
import threading
import time
from datetime import datetime, timedelta
from telebot import TeleBot, types

# =====================
# CONFIGURAÇÕES
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")

VIP_GROUP_ID = -2575039597  # ID do grupo VIP

bot = TeleBot(BOT_TOKEN)

# =====================
# BANCO DE DADOS
# =====================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    user_id INTEGER PRIMARY KEY,
    idioma TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pagamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    plano TEXT,
    payment_id TEXT,
    status TEXT,
    criado_em TEXT,
    vence_em TEXT
)
""")
conn.commit()

# =====================
# MENSAGENS POR IDIOMA
# =====================
mensagens = {
    "pt": {
        "inicio": "Oi, primo! Eu estou tomando banho, mas sou nova por aqui... sinto que está faltando algo aqui comigo, acho que pode ser você!",
        "botao_inicio": "Claro que te ajudo, prima!",
        "video_caption": "🌶️  Você bem que poderia vir aqui me dar uma ajudinha com isso, estou toda molhada!💦   Pode me ajudar?",
        "msg1": "🙈Estou muito ansiosa por isso priminho, só falta você aqui pra ficar tudo perfeito!\n\n"
                "🔥Sabe como é né, tenho 23 aninhos e tenho muito tesão...\n\n"
                "🔑 Vou te dar a chave da minha casa, assim você pode entrar quando quiser 😏",
        "botao_chave": "Quero a chave da sua casa, priminha",
        "planos_texto": "😈 Assim que o pagamento for confirmado, você será adicionada automaticamente ao meu Grupo VIP 🔥\n\nEscolha o plano 👇",
        "pix_msg": "🔑 Copie e cole o código Pix abaixo no seu banco:",
        "pix_erro": "Erro ao gerar o Pix.",
        "pago": "🔥 Pagamento confirmado! Já te coloquei no grupo 😈",
        "vencido": "⏳ Seu acesso venceu, amor... Quer renovar?"
    },
    "es": {
        "inicio": "¡Hola, primo! Estoy en la ducha y soy nueva por aquí...",
        "botao_inicio": "¡Claro que te ayudo!",
        "video_caption": "🌶️ ¿Puedes venir a ayudarme? Estoy toda mojada 💦",
        "msg1": "🙈 Estoy muy ansiosa por esto...",
        "botao_chave": "Quiero la llave de tu casa",
        "planos_texto": "😈 Elige tu plan 👇",
        "pix_msg": "🔑 Copia y pega el código Pix abajo:",
        "pix_erro": "Error al generar el pago.",
        "pago": "🔥 Pago confirmado! Ya estás en el grupo 😈",
        "vencido": "⏳ Tu acceso expiró. ¿Renovar?"
    },
    "en": {
        "inicio": "Hey! I'm in the shower and new here...",
        "botao_inicio": "Sure, I’ll help!",
        "video_caption": "🌶️ Can you help me? I'm all wet 💦",
        "msg1": "🙈 I'm really excited...",
        "botao_chave": "I want your house key",
        "planos_texto": "😈 Choose your plan 👇",
        "pix_msg": "🔑 Copy and paste the Pix code below:",
        "pix_erro": "Error generating payment.",
        "pago": "🔥 Payment confirmed! You're in 😈",
        "vencido": "⏳ Your access expired. Renew?"
    }
}

idiomas_usuarios = {}

# =====================
# MERCADO PAGO
# =====================
def criar_pix(valor):
    url = "https://api.mercadopago.com/v1/payments"
    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4())
    }
    data = {
        "transaction_amount": float(valor),
        "payment_method_id": "pix",
        "payer": {"email": "cliente@exemplo.com"}
    }
    r = requests.post(url, headers=headers, json=data)
    if r.status_code == 201:
        j = r.json()
        return j["id"], j["point_of_interaction"]["transaction_data"]["qr_code"]
    return None, None

def consultar_pagamento(payment_id):
    r = requests.get(
        f"https://api.mercadopago.com/v1/payments/{payment_id}",
        headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
    )
    if r.status_code == 200:
        return r.json()["status"]
    return None

# =====================
# VERIFICA PAGAMENTOS
# =====================
def verificar_pagamentos():
    while True:
        cursor.execute("SELECT id, user_id, payment_id, plano FROM pagamentos WHERE status='pending'")
        for pid, user_id, payment_id, plano in cursor.fetchall():
            if consultar_pagamento(payment_id) == "approved":
                vence = None
                if plano != "vitalicio":
                    dias = 30 if plano == "30" else 90
                    vence = (datetime.now() + timedelta(days=dias)).isoformat()

                cursor.execute("UPDATE pagamentos SET status='approved', vence_em=? WHERE id=?", (vence, pid))
                conn.commit()

                try:
                    bot.add_chat_member(VIP_GROUP_ID, user_id)
                except:
                    pass

                lang = idiomas_usuarios.get(user_id, "pt")
                bot.send_message(user_id, mensagens[lang]["pago"])

        time.sleep(30)

# =====================
# START / IDIOMA
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇧🇷 Português", callback_data="lang_pt"))
    markup.add(types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"))
    markup.add(types.InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"))

    bot.send_message(
        message.chat.id,
        "Escolha seu idioma / Choose your language / Elige tu idioma:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def idioma(call):
    lang = call.data.split("_")[1]
    chat_id = call.message.chat.id
    idiomas_usuarios[chat_id] = lang

    cursor.execute("INSERT OR REPLACE INTO usuarios (user_id, idioma) VALUES (?,?)", (chat_id, lang))
    conn.commit()

    bot.send_message(chat_id, mensagens[lang]["inicio"])

    with open("midia/video01.mp4", "rb") as video:
        bot.send_video(chat_id, video, caption=mensagens[lang]["video_caption"])

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(mensagens[lang]["botao_inicio"], callback_data="ajuda"))
    bot.send_message(chat_id, mensagens[lang]["botao_inicio"], reply_markup=markup)

# =====================
# AJUDA
# =====================
@bot.callback_query_handler(func=lambda call: call.data == "ajuda")
def ajuda(call):
    chat_id = call.message.chat.id
    lang = idiomas_usuarios.get(chat_id, "pt")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(mensagens[lang]["botao_chave"], callback_data="planos"))
    bot.send_message(chat_id, mensagens[lang]["msg1"], reply_markup=markup)

# =====================
# PLANOS
# =====================
@bot.callback_query_handler(func=lambda call: call.data == "planos")
def planos(call):
    chat_id = call.message.chat.id
    lang = idiomas_usuarios.get(chat_id, "pt")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("30 dias - R$20", callback_data="30"))
    markup.add(types.InlineKeyboardButton("90 dias - R$30", callback_data="90"))
    markup.add(types.InlineKeyboardButton("Vitalício - R$50", callback_data="vitalicio"))

    bot.send_message(chat_id, mensagens[lang]["planos_texto"], reply_markup=markup)

# =====================
# PAGAR
# =====================
@bot.callback_query_handler(func=lambda call: call.data in ["30", "90", "vitalicio"])
def pagar(call):
    chat_id = call.message.chat.id
    plano = call.data
    valor = 20 if plano == "30" else 30 if plano == "90" else 50

    payment_id, pix = criar_pix(valor)
    if not pix:
        bot.send_message(chat_id, "Erro ao gerar Pix.")
        return

    cursor.execute(
        "INSERT INTO pagamentos (user_id, plano, payment_id, status, criado_em) VALUES (?, ?, ?, 'pending', ?)",
        (chat_id, plano, payment_id, datetime.now().isoformat())
    )
    conn.commit()

    lang = idiomas_usuarios.get(chat_id, "pt")
    bot.send_message(chat_id, mensagens[lang]["pix_msg"])
    bot.send_message(chat_id, pix)

# =====================
# THREADS
# =====================
threading.Thread(target=verificar_pagamentos, daemon=True).start()

# =====================
# START BOT
# =====================
bot.infinity_polling()
