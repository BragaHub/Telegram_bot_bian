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

DB_PATH = "bot.db"

# =====================
# BANCO DE DADOS
# =====================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn, conn.cursor()

def init_db():
    conn, cursor = get_db()

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
    conn.close()

init_db()

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
# VERIFICAR PAGAMENTOS
# =====================
def verificar_pagamentos():
    while True:
        conn, cursor = get_db()
        cursor.execute("SELECT id, user_id, payment_id, plano FROM pagamentos WHERE status='pending'")
        pendentes = cursor.fetchall()

        for pid, user_id, payment_id, plano in pendentes:
            status = consultar_pagamento(payment_id)
            if status == "approved":
                vence = None
                if plano != "vitalicio":
                    dias = 30 if plano == "30" else 90
                    vence = (datetime.now() + timedelta(days=dias)).isoformat()

                cursor.execute("""
                UPDATE pagamentos SET status='approved', vence_em=?
                WHERE id=?
                """, (vence, pid))
                conn.commit()

                try:
                    bot.add_chat_member(VIP_GROUP_ID, user_id)
                except:
                    pass

                lang = idiomas_usuarios.get(user_id, "pt")
                bot.send_message(user_id, mensagens[lang]["pago"])

        conn.close()
        time.sleep(30)

# =====================
# VERIFICAR VENCIMENTOS
# =====================
def verificar_vencimentos():
    while True:
        conn, cursor = get_db()
        cursor.execute("""
        SELECT user_id, vence_em FROM pagamentos
        WHERE status='approved' AND plano!='vitalicio'
        """)
        ativos = cursor.fetchall()

        for user_id, vence in ativos:
            if vence and datetime.fromisoformat(vence) < datetime.now():
                try:
                    bot.ban_chat_member(VIP_GROUP_ID, user_id)
                    bot.unban_chat_member(VIP_GROUP_ID, user_id)
                except:
                    pass

                lang = idiomas_usuarios.get(user_id, "pt")
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Renovar 🔥", callback_data="planos"))

                bot.send_message(user_id, mensagens[lang]["vencido"], reply_markup=markup)

                cursor.execute("""
                UPDATE pagamentos SET status='expired'
                WHERE user_id=?
                """, (user_id,))
                conn.commit()

        conn.close()
        time.sleep(3600)

# =====================
# TELEGRAM
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇧🇷 Português", callback_data="lang_pt")
    )
    bot.send_message(message.chat.id, "Escolha seu idioma:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def idioma(call):
    lang = call.data.split("_")[1]
    chat_id = call.message.chat.id
    idiomas_usuarios[chat_id] = lang

    conn, cursor = get_db()
    cursor.execute("INSERT OR REPLACE INTO usuarios VALUES (?,?)", (chat_id, lang))
    conn.commit()
    conn.close()

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(mensagens[lang]["botao_inicio"], callback_data="ajuda"))

    bot.send_message(chat_id, mensagens[lang]["inicio"])
    with open("midia/video01.mp4", "rb") as video:
        bot.send_video(chat_id, video, caption=mensagens[lang]["video_caption"], reply_markup=markup)

# =====================
# THREADS
# =====================
threading.Thread(target=verificar_pagamentos, daemon=True).start()
threading.Thread(target=verificar_vencimentos, daemon=True).start()

bot.infinity_polling()



