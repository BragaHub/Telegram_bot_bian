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
# MENSAGENS / ROTEIRO
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
                        " - Trisal\n"
                        " - Siririca com brinquedos\n"
                        " - Gozando intensamente 💦\n\n"
                        "🎁 Plano 90 dias (R$30): sorteio semanal de videochamada comigo!\n\n"
                        "🎥 Plano Vitalício (R$50): sorteio mensal de um dia de gravações comigo 😏\n\n"
                        "Escolha o plano 👇🏼",
        "pix_msg": "🔑 Para pagar, copie e cole o Pix abaixo no seu banco:",
        "pix_erro": "Erro ao gerar o Pix. Tente novamente."
    },
    "es": {
        "inicio": "¡Hola, primo! Estoy en la ducha y soy nueva por aquí... siento que algo me falta, ¡creo que podrías ser tú!",
        "botao_inicio": "¡Claro que te ayudo, prima!",
        "video_caption": "🌶️ Podrías venir a ayudarme con esto, estoy toda mojada 💦 ¿Me ayudas?",
        "msg1": "🙈Estoy muy ansiosa por esto.\n\n🔥 Tengo 23 añitos y mucho deseo 😏\n\n🔑 Te daré la llave de mi casa...",
        "botao_chave": "Quiero la llave de tu casa",
        "planos_texto": "😈 Acceso total a mi Grupo VIP con contenido exclusivo.\n\nElige tu plan 👇🏼",
        "pix_msg": "🔑 Copia y pega el Pix abajo:",
        "pix_erro": "Error al generar el Pix."
    },
    "en": {
        "inicio": "Hey, cousin! I'm in the shower and new around here... maybe you're what I'm missing!",
        "botao_inicio": "Sure, I’ll help you!",
        "video_caption": "🌶️ I’m all wet 💦 Can you help me?",
        "msg1": "🙈I'm really excited...\n\n🔥 I'm 23 and very horny 😏\n\n🔑 I'll give you my house key...",
        "botao_chave": "I want the key",
        "planos_texto": "😈 Full access to my VIP Group.\n\nChoose a plan 👇🏼",
        "pix_msg": "🔑 Copy and paste the Pix below:",
        "pix_erro": "Error generating Pix."
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

# =====================
# START
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇧🇷 Português", callback_data="lang_pt"),
        types.InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
    )
    bot.send_message(message.chat.id, "Escolha seu idioma:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def idioma(call):
    lang = call.data.split("_")[1]
    chat_id = call.message.chat.id
    idiomas_usuarios[chat_id] = lang

    bot.send_message(chat_id, mensagens[lang]["inicio"])

    with open("midia/video01.mp4", "rb") as video:
        bot.send_video(chat_id, video, caption=mensagens[lang]["video_caption"])

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        mensagens[lang]["botao_inicio"],
        callback_data="ajuda"
    ))
    bot.send_message(chat_id, mensagens[lang]["botao_inicio"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "ajuda")
def ajuda(call):
    lang = idiomas_usuarios.get(call.message.chat.id, "pt")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        mensagens[lang]["botao_chave"],
        callback_data="planos"
    ))
    bot.send_message(call.message.chat.id, mensagens[lang]["msg1"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "planos")
def planos(call):
    lang = idiomas_usuarios.get(call.message.chat.id, "pt")
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("30 dias - R$20", callback_data="30"),
        types.InlineKeyboardButton("90 dias - R$30", callback_data="90"),
        types.InlineKeyboardButton("Vitalício - R$50", callback_data="vitalicio")
    )
    bot.send_message(call.message.chat.id, mensagens[lang]["planos_texto"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["30", "90", "vitalicio"])
def pagar(call):
    chat_id = call.message.chat.id
    plano = call.data
    valor = 20 if plano == "30" else 30 if plano == "90" else 50

    payment_id, pix = criar_pix(valor)
    lang = idiomas_usuarios.get(chat_id, "pt")

    if not pix:
        bot.send_message(chat_id, mensagens[lang]["pix_erro"])
        return

    bot.send_message(chat_id, mensagens[lang]["pix_msg"])
    bot.send_message(chat_id, pix)

# =====================
# START BOT
# =====================
bot.infinity_polling()
