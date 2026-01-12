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

VIP_GROUP_ID = -2575039597

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
# MENSAGENS
# =====================
mensagens = {
    "pt": {
        "inicio": "Oi, primo! Eu estou tomando banho...",
        "botao_inicio": "Claro que te ajudo, prima!",
        "video_caption": "🌶️ Você bem que poderia vir aqui me dar uma ajudinha...",
        "msg1": "🙈 Estou muito ansiosa por isso...",
        "botao_chave": "Quero a chave da sua casa",
        "planos": "Escolha o plano 👇",
        "pix": "🔑 Copie e cole o Pix abaixo:",
        "pago": "🔥 Pagamento confirmado! Já te coloquei no grupo 😈",
        "vencido": "⏳ Seu acesso venceu, amor...\nQuer renovar?",
    }
}

idiomas_usuarios = {}

# =====================
# MERCADO PAGO
# =====================
def criar_pix(valor):
    r = requests.post(
        "https://api.mercadopago.com/v1/payments",
        headers={
            "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Idempotency-Key": str(uuid.uuid4())
        },
        json={
            "transaction_amount": float(valor),
            "payment_method_id": "pix",
            "payer": {"email": "cliente@exemplo.com"}
        }
    )
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
# BACKGROUND JOBS
# =====================
def verificar_pagamentos():
    while True:
        cursor.execute(
            "SELECT id, user_id, payment_id, plano FROM pagamentos WHERE status='pending'"
        )
        for pid, user_id, payment_id, plano in cursor.fetchall():
            if consultar_pagamento(payment_id) == "approved":
                vence = None
                if plano != "vitalicio":
                    dias = 30 if plano == "30" else 90
                    vence = (datetime.now() + timedelta(days=dias)).isoformat()

                cursor.execute(
                    "UPDATE pagamentos SET status='approved', vence_em=? WHERE id=?",
                    (vence, pid)
                )
                conn.commit()

                try:
                    bot.add_chat_member(VIP_GROUP_ID, user_id)
                except:
                    pass

                bot.send_message(user_id, mensagens["pt"]["pago"])

        time.sleep(30)

def verificar_vencimentos():
    while True:
        cursor.execute("""
        SELECT user_id, vence_em FROM pagamentos
        WHERE status='approved' AND plano!='vitalicio'
        """)
        for user_id, vence in cursor.fetchall():
            if vence and datetime.fromisoformat(vence) < datetime.now():
                try:
                    bot.ban_chat_member(VIP_GROUP_ID, user_id)
                    bot.unban_chat_member(VIP_GROUP_ID, user_id)
                except:
                    pass

                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Renovar 🔥", callback_data="planos"))

                bot.send_message(
                    user_id,
                    mensagens["pt"]["vencido"],
                    reply_markup=markup
                )

                cursor.execute(
                    "UPDATE pagamentos SET status='expired' WHERE user_id=?",
                    (user_id,)
                )
                conn.commit()

        time.sleep(3600)

# =====================
# HANDLERS
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇧🇷 Português", callback_data="lang_pt"))
 bot.send_message(
    message.chat.id,
    "Escolha seu idioma:",
    reply_markup=markup
)


@bot.callback_query_handler(func=lambda c: c.data == "lang_pt")
def idioma(call):
    chat_id = call.message.chat.id
    idiomas_usuarios[chat_id] = "pt"

    bot.send_message(chat_id, mensagens["pt"]["inicio"])

    with open("midia/video01.mp4", "rb") as video:
        bot.send_video(chat_id, video, caption=mensagens["pt"]["video_caption"])

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        mensagens["pt"]["botao_inicio"],
        callback_data="ajuda"
    ))

    bot.send_message(
    message.chat.id,
    "Escolha seu idioma:",
    reply_markup=markup
)

@bot.callback_query_handler(func=lambda c: c.data == "ajuda")
def ajuda(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        mensagens["pt"]["botao_chave"],
        callback_data="planos"
    ))
    bot.send_message(call.message.chat.id, mensagens["pt"]["msg1"], reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "planos")
def planos(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("30 dias - R$20", callback_data="30"),
        types.InlineKeyboardButton("90 dias - R$30", callback_data="90"),
        types.InlineKeyboardButton("Vitalício - R$50", callback_data="vitalicio")
    )
    bot.send_message(call.message.chat.id, mensagens["pt"]["planos"], reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data in ["30", "90", "vitalicio"])
def pagar(call):
    valor = 20 if call.data == "30" else 30 if call.data == "90" else 50
    payment_id, pix = criar_pix(valor)

    if not pix:
        bot.send_message(call.message.chat.id, "Erro ao gerar Pix.")
        return

    cursor.execute("""
    INSERT INTO pagamentos (user_id, plano, payment_id, status, criado_em)
    VALUES (?, ?, ?, 'pending', ?)
    """, (call.message.chat.id, call.data, payment_id, datetime.now().isoformat()))
    conn.commit()

    bot.send_message(call.message.chat.id, mensagens["pt"]["pix"])
    bot.send_message(call.message.chat.id, pix)

# =====================
# STARTUP
# =====================
def start_background_jobs():
    threading.Thread(target=verificar_pagamentos, daemon=True).start()
    threading.Thread(target=verificar_vencimentos, daemon=True).start()

start_background_jobs()

bot.infinity_polling(
    skip_pending=True,
    timeout=30,
    long_polling_timeout=30
)





