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
# MENSAGENS (NÃO ALTERADAS)
# =====================
mensagens = {
    "pt": {
        "inicio": "Oi, primo! Eu estou tomando banho, mas sou nova por aqui... sinto que está faltando algo aqui comigo, acho que pode ser você!",
        "botao_inicio": "Claro que te ajudo, prima!",
        "video_caption": "🌶️  Você bem que poderia vir aqui me dar uma ajudinha com isso, estou toda molhada!💦   Pode me ajudar?",
        "msg1": "🙈Estou muito ansiosa por isso priminho, só falta você aqui pra ficar tudo perfeito!\n\n"
                "🔥Sabe como é né, tenho 23 aninhos e tenho muito tesão, espero que você esteja pronto para o que está por vir... 😏\n\n"
                "🔑 Sabe o que eu estou pensando... vou te dar a chave da minha casa, assim você pode entrar e me ver peladinha quando quiser, que tal?",
        "botao_chave": "Quero a chave da sua casa, priminha",
        "planos_texto": "😈 Vou te dar a chave da minha casa... Esse vai ser nosso segredinho, tá bom?\n\n"
                        "Assim que o pagamento for confirmado, você será adicionado automaticamente ao meu Grupo VIP aqui no Telegram, com acesso a todo o meu conteúdo exclusivo! ⚜️🔥\n\n"
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
        "inicio": "¡Hola, primo! Estoy en la ducha y soy nueva por aquí... siento que algo me falta, ¡creo que podrías ser tú!",
        "botao_inicio": "¡Claro que te ayudo, prima!",
        "video_caption": "🌶️ Podrías venir a ayudarme con esto, estoy toda mojada 💦 ¿Me ayudas?",
        "msg1": "🙈Estoy muy ansiosa por esto, primito. Solo faltas tú para que todo sea perfecto.\n\n"
                "🔥Ya sabes, tengo 23 añitos y mucho deseo... Espero que estés listo para lo que viene 😏\n\n"
                "🔑 Estaba pensando... Te voy a dar la llave de mi casa, así puedes verme desnuda cuando quieras, ¿te gusta?",
        "botao_chave": "Quiero la llave de tu casa, primita",
        "planos_texto": "😈 Te voy a dar la llave de mi casa... Será nuestro secretito, ¿vale?\n\n"
                        "Una vez confirmado el pago, serás añadido automáticamente a mi Grupo VIP aquí en Telegram con acceso a todo mi contenido exclusivo! ⚜️🔥\n\n"
                        "💎 VIDEOS EXCLUSIVOS:\n"
                        " - Sexo anal\n"
                        " - Sexo oral\n"
                        " - Trío con amigas\n"
                        " - Masturbación con juguetes\n"
                        " - Orgasmos intensos 💦\n\n"
                        "🎁 Suscriptores del plan de 90 días (R$50) participan en un sorteo semanal por una videollamada conmigo!\n\n"
                        "🎥 Vitalício (R$100) participan cada mes por un día de grabaciones conmigo — tú al mando. 😏",
        "pix_msg": "🔑 Usa el QR Code abajo o copia y pega el código Pix en tu banco:",
        "pix_erro": "Lo siento, hubo un error al generar el pago. Intenta de nuevo más tarde."
    },
    "en": {
        "inicio": "Hey, cousin! I'm in the shower and new around here... I feel like something's missing — maybe it's you!",
        "botao_inicio": "Sure, I’ll help you, cousin!",
        "video_caption": "🌶️ Maybe you could come and help me with this, I’m all wet 💦 Can you help me?",
        "msg1": "🙈I’m really excited about this, cousin. Just need you here to make it perfect!\n\n"
                "🔥You know... I’m 23 and really horny. I hope you're ready for what’s coming 😏\n\n"
                "🔑 I was thinking... I’ll give you the key to my house, so you can see me naked whenever you want. Sounds good?",
        "botao_chave": "I want your house key, cousin",
        "planos_texto": "😈 I'll give you the key to my house... It’ll be our little secret, okay?\n\n"
                        "Once payment is confirmed, you’ll be added automatically to my VIP Group here on Telegram with access to all my exclusive content! ⚜️🔥\n\n"
                        "💎 EXCLUSIVE VIDEOS:\n"
                        " - Anal sex\n"
                        " - Blowjob\n"
                        " - Threesome\n"
                        " - Toy play\n"
                        " - Intense orgasms 💦\n\n"
                        "🎁 90-day subscribers (R$50) enter a weekly draw for a video call with me!\n\n"
                        "🎥 Lifetime plan subscribers (R$100) enter a monthly draw to direct a full shoot with me 😏",
        "pix_msg": "🔑 Use the QR Code below or copy and paste the Pix code into your bank app:",
        "pix_erro": "Sorry, there was an error generating the payment. Please try again later."
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
    r = requests.get(
        f"https://api.mercadopago.com/v1/payments/{payment_id}",
        headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
    )
    if r.status_code == 200:
        return r.json()["status"]
    return None

# =====================
# START
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

# =====================
# IDIOMA
# =====================
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

# =====================
# AJUDA
# =====================
@bot.callback_query_handler(func=lambda call: call.data == "ajuda")
def ajuda(call):
    lang = idiomas_usuarios.get(call.message.chat.id, "pt")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(mensagens[lang]["botao_chave"], callback_data="planos"))
    bot.send_message(call.message.chat.id, mensagens[lang]["msg1"], reply_markup=markup)

# =====================
# PLANOS
# =====================
@bot.callback_query_handler(func=lambda call: call.data == "planos")
def planos(call):
    lang = idiomas_usuarios.get(call.message.chat.id, "pt")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("30 dias - R$25", callback_data="30"))
    markup.add(types.InlineKeyboardButton("90 dias - R$50", callback_data="90"))
    markup.add(types.InlineKeyboardButton("Vitalício - R$100", callback_data="vitalicio"))
    bot.send_message(call.message.chat.id, mensagens[lang]["planos_texto"], reply_markup=markup)

# =====================
# PAGAMENTO (COM QR CODE)
# =====================
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
# VERIFICAR PAGAMENTOS
# =====================
def verificar_pagamentos():
    while True:
        cursor.execute("SELECT id, user_id, payment_id FROM pagamentos WHERE status='pending'")
        for pid, user_id, payment_id in cursor.fetchall():
            status = consultar_pagamento(payment_id)
            if status == "approved":
                cursor.execute("UPDATE pagamentos SET status='approved' WHERE id=?", (pid,))
                conn.commit()
                try:
                    bot.add_chat_member(VIP_GROUP_ID, user_id)
                except:
                    pass
        time.sleep(30)

threading.Thread(target=verificar_pagamentos, daemon=True).start()

# =====================
# START BOT
# =====================
bot.infinity_polling()




