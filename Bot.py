import os
import uuid
import sqlite3
import requests
import threading
import time
import qrcode
from io import BytesIO
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
        "inicio": "Oi, amor! Eu estou tomando banho, mas sou nova por aqui... sinto que está faltando algo aqui comigo, acho que pode ser você!",
        "botao_inicio": "Claro que te ajudo, prima!",
        "video_caption": "🌶️  Você bem que poderia vir aqui me dar uma ajudinha com isso, estou toda molhada!💦   Pode me ajudar?",
        "msg1": "🙈Estou muito ansiosa por isso priminho, só falta você aqui pra ficar tudo perfeito!\n\n"
                "🔥Sabe como é né, tenho 23 aninhos e tenho muito tesão, espero que você esteja pronto para o que está por vir... 😏\n\n"
                "🔑 Sabe o que eu estou pensando... vou te dar a chave da minha casa, assim você pode entrar e me ver peladinha quando quiser, que tal?",
        "botao_chave": "Quero a chave da sua casa, priminha",
        "planos_texto": "😈 Vou te dar a chave da minha casa... Esse vai ser nosso segredinho, tá bom?\n\n"
                        "Assim que o pagamento for confirmado, você receberá automaticamente o acesso ao meu Grupo VIP aqui no Telegram! ⚜️🔥\n\n"
                        "💎 VÍDEOS EXCLUSIVOS:\n"
                        " - Sexo anal\n"
                        " - Boquete\n"
                        " - Trisal (sexo com amigas)\n"
                        " - Siririca com brinquedos\n"
                        " - Gozando intensamente 💦\n\n"
                        "🎁 Assinantes do plano de 90 dias (R$50) participam de um sorteio semanal valendo videochamada comigo!\n\n"
                        "🎥 Assinantes do plano Vitalício (R$100) concorrem todo mês a um dia de gravações comigo — você no comando. 😏\n\n"
                        "Escolha o plano que deseja e vem pro meu mundo... 👇🏼",
        "pix_msg": "🔑 Para fazer o pagamento, use o QR Code abaixo ou copie e cole o código Pix no seu banco:",
        "pix_erro": "Desculpe, houve um erro ao gerar o pagamento Pix. Tente novamente mais tarde."
    },
    "es": {
        "inicio": "¡Hola, amor! Estoy en la ducha y soy nueva por aquí... siento que algo me falta, ¡creo que podrías ser tú!",
        "botao_inicio": "¡Claro que te ayudo, prima!",
        "video_caption": "🌶️ Podrías venir a ayudarme con esto, estoy toda mojada 💦 ¿Me ayudas?",
        "msg1": "🙈Estoy muy ansiosa por esto, primito. Solo faltas tú para que todo sea perfecto.\n\n"
                "🔥Ya sabes, tengo 23 añitos y mucho deseo... Espero que estés listo para lo que viene 😏\n\n"
                "🔑 Estaba pensando... Te voy a dar la llave de mi casa, así puedes verme desnuda cuando quieras, ¿te gusta?",
        "botao_chave": "Quiero la llave de tu casa, primita",
        "planos_texto": "😈 Te voy a dar la llave de mi casa... Será nuestro secretito, ¿vale?\n\n"
                        "Una vez confirmado el pago, recibirás el acceso automático al grupo VIP!\n\n"
                        "💎 VIDEOS EXCLUSIVOS...\n",
        "pix_msg": "🔑 Usa el QR Code abajo o copia y pega el código Pix en tu banco:",
        "pix_erro": "Lo siento, hubo un error al generar el pago."
    },
    "en": {
        "inicio": "Hey, my love! I'm in the shower and new around here...",
        "botao_inicio": "Sure, I’ll help you!",
        "video_caption": "🌶️ Can you help me?",
        "msg1": "🙈I’m really excited...",
        "botao_chave": "I want access",
        "planos_texto": "😈 Choose your plan...",
        "pix_msg": "Use QR Code:",
        "pix_erro": "Payment error."
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

def gerar_qr_code(pix_code):
    img = qrcode.make(pix_code)
    bio = BytesIO()
    bio.name = "pix_qr.png"
    img.save(bio, "PNG")
    bio.seek(0)
    return bio

def consultar_pagamento(payment_id):
    try:
        r = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
        )
        if r.status_code == 200:
            return r.json()["status"]
    except:
        pass
    return None

# =====================
# FLUXO
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇧🇷 Português", callback_data="lang_pt"))
    markup.add(types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"))
    markup.add(types.InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"))

    bot.send_message(message.chat.id, "Escolha idioma:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def idioma(call):
    lang = call.data.split("_")[1]
    chat_id = call.message.chat.id
    idiomas_usuarios[chat_id] = lang

    bot.send_message(chat_id, mensagens[lang]["inicio"])

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(mensagens[lang]["botao_inicio"], callback_data="ajuda"))

    with open("midia/video01.mp4", "rb") as video:
        bot.send_video(chat_id, video, caption=mensagens[lang]["video_caption"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "ajuda")
def ajuda(call):
    lang = idiomas_usuarios.get(call.message.chat.id, "pt")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(mensagens[lang]["botao_chave"], callback_data="planos"))
    bot.send_message(call.message.chat.id, mensagens[lang]["msg1"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "planos")
def planos(call):
    lang = idiomas_usuarios.get(call.message.chat.id, "pt")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("30 dias - R$25", callback_data="30"))
    markup.add(types.InlineKeyboardButton("90 dias - R$50", callback_data="90"))
    markup.add(types.InlineKeyboardButton("Vitalício - R$100", callback_data="vitalicio"))
    bot.send_message(call.message.chat.id, mensagens[lang]["planos_texto"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["30", "90", "vitalicio"])
def pagar(call):
    chat_id = call.message.chat.id
    plano = call.data
    valor = 25 if plano == "30" else 50 if plano == "90" else 100

    payment_id, pix = criar_pix(valor)
    lang = idiomas_usuarios.get(chat_id, "pt")

    if not pix:
        bot.send_message(chat_id, mensagens[lang]["pix_erro"])
        return

    cursor.execute("""
        INSERT INTO pagamentos (user_id, plano, payment_id, status, criado_em)
        VALUES (?, ?, ?, 'pending', ?)
    """, (chat_id, plano, payment_id, datetime.now().isoformat()))
    conn.commit()

    qr_img = gerar_qr_code(pix)

    bot.send_message(chat_id, mensagens[lang]["pix_msg"])
    bot.send_photo(chat_id, qr_img)
    bot.send_message(chat_id, pix)

# =====================
# CORREÇÃO AQUI
# =====================
def verificar_pagamentos():
    while True:
        try:
            cursor.execute("SELECT id, user_id, payment_id FROM pagamentos WHERE status='pending'")
            pagamentos = cursor.fetchall()

            for pid, user_id, payment_id in pagamentos:
                status = consultar_pagamento(payment_id)

                if status in ["approved", "authorized"]:
                    cursor.execute("UPDATE pagamentos SET status='approved' WHERE id=?", (pid,))
                    conn.commit()

                    invite_link = bot.create_chat_invite_link(VIP_GROUP_ID, member_limit=1)

                    bot.send_message(
                        user_id,
                        f"🔥 Pagamento aprovado!\n\nAcesse seu VIP:\n{invite_link.invite_link}"
                    )

        except Exception as e:
            print(f"ERRO: {e}")

        time.sleep(15)

threading.Thread(target=verificar_pagamentos, daemon=True).start()

bot.infinity_polling()



