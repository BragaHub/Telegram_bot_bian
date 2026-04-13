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

BOT_TOKEN = os.getenv("BOT_TOKEN")
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")

VIP_GROUP_ID = -1002575039597

bot = TeleBot(BOT_TOKEN)

# =====================
# BANCO
# =====================
conn = sqlite3.connect("bot.db", check_same_thread=False)

def get_cursor():
    return conn.cursor()

cursor = get_cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS pagamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    plano TEXT,
    payment_id TEXT,
    status TEXT,
    criado_em TEXT,
    vence_em TEXT,
    removido INTEGER DEFAULT 0,
    qr_enviado INTEGER DEFAULT 0
)
""")
conn.commit()

# =====================
# MENSAGENS
# =====================
mensagens = {
    "pt": {
        "inicio": "Oi, amor! Eu estou tomando banho, mas sou nova por aqui... sinto que está faltando algo aqui comigo, acho que pode ser você!",
        "botao_inicio": "Claro que te ajudo, amor!",
        "video_caption": "🌶️  Você bem que poderia vir aqui me dar uma ajudinha com isso, estou toda molhada!💦   Pode me ajudar?",
        "msg1": "🙈Estou muito ansiosa por isso amorzinho, só falta você aqui pra ficar tudo perfeito!\n\n"
                "🔥Sabe como é né, tenho 24 aninhos e tenho muito tesão, espero que você esteja pronto para o que está por vir... 😏\n\n"
                "🔑 Sabe o que eu estou pensando... vou te dar a chave da minha casa, assim você pode entrar e me ver peladinha quando quiser, que tal?",
        "botao_chave": "Quero a chave da sua casa, meu amor",
        "planos_texto": "😈 Vou te dar a chave da minha casa... Esse vai ser nosso segredinho, tá bom?\n\n"
                        "Assim que o pagamento for confirmado, você receberá o link do meu Grupo VIP com acesso a todo o meu conteúdo exclusivo! ⚜️🔥\n\n"
                        "Obs.: Link de uso único, ao compartilhar o link você poderá perder o acesso.\n\n"
                        "💎 VÍDEOS EXCLUSIVOS:\n"
                        " - Sexo anal\n"
                        " - Boquete\n"
                        " - Trisal (sexo com amigas)\n"
                        " - Siririca com brinquedos\n"
                        " - Gozando intensamente 💦\n\n"
                        "🎁 Assinantes do plano de 90 dias (R$59,90) participam de um sorteio semanal valendo videochamada comigo!\n\n"
                        "🎥 Assinantes do plano Vitalício (R$119,90) concorrem todo mês a um dia de gravações comigo — você no comando. 😏\n\n"
                        "Escolha o plano que deseja e vem pro meu mundo... 👇🏼",
        "pix_msg": "🔑 Para fazer o pagamento, use o QR Code abaixo ou copie e cole o código Pix no seu banco:",
        "pix_erro": "Desculpe, houve um erro ao gerar o pagamento Pix. Tente novamente mais tarde."
    },
    "es": {
        "inicio": "¡Hola, amor! Estoy en la ducha y soy nueva por aquí... siento que algo me falta, ¡creo que podrías ser tú!",
        "botao_inicio": "¡Claro que te ayudo, mi amor!",
        "video_caption": "🌶️ Podrías venir a ayudarme con esto, estoy toda mojada 💦 ¿Me ayudas?",
        "msg1": "🙈Estoy muy ansiosa por esto, mi amor. Solo faltas tú para que todo sea perfecto.\n\n"
                "🔥Ya sabes, tengo 24 añitos y mucho deseo... Espero que estés listo para lo que viene 😏\n\n"
                "🔑 Estaba pensando... Te voy a dar la llave de mi casa, así puedes verme desnuda cuando quieras, ¿te gusta?",
        "botao_chave": "Quiero la llave de tu casa, amor",
        "planos_texto": "😈 Te voy a dar la llave de mi casa... Será nuestro secretito, ¿vale?\n\n"
                        "Una vez confirmado el pago, recibirás el enlace a mi Grupo VIP con acceso a todo mi contenido exclusivo. ⚜️🔥\n\n"
                        "Nota: Este enlace es de un solo uso; compartirlo podría resultar en la pérdida del acceso.\n\n"
                        "💎 VIDEOS EXCLUSIVOS:\n"
                        " - Sexo anal\n"
                        " - Sexo oral\n"
                        " - Trío con amigas\n"
                        " - Masturbación con juguetes\n"
                        " - Orgasmos intensos 💦\n\n"
                        "🎁 Suscriptores del plan de 90 días (R$59,90) participan en un sorteo semanal por una videollamada conmigo!\n\n"
                        "🎥 Vitalício (R$119,90) participan cada mes por un día de grabaciones conmigo — tú al mando. 😏",
        "pix_msg": "🔑 Usa el QR Code abajo o copia y pega el código Pix en tu banco:",
        "pix_erro": "Lo siento, hubo un error al generar el pago. Intenta de nuevo más tarde."
    },
    "en": {
        "inicio": "Hey, love! I'm in the shower and new around here... I feel like something's missing — maybe it's you!",
        "botao_inicio": "Sure, I’ll help you, love!",
        "video_caption": "🌶️ Maybe you could come and help me with this, I’m all wet 💦 Can you help me?",
        "msg1": "🙈I’m really excited about this, my love. Just need you here to make it perfect!\n\n"
                "🔥You know... I’m 24 and really horny. I hope you're ready for what’s coming 😏\n\n"
                "🔑 I was thinking... I’ll give you the key to my house, so you can see me naked whenever you want. Sounds good?",
        "botao_chave": "I want your house key, lovin",
        "planos_texto": "😈 I'll give you the key to my house... It’ll be our little secret, okay?\n\n"
                        "Once payment is confirmed, you will receive the link to my VIP Group with access to all my exclusive content! ⚜️🔥\n\n"
                        "Note: This is a one-time-use link; sharing it may result in the loss of access.\n\n"
                        "💎 EXCLUSIVE VIDEOS:\n"
                        " - Anal sex\n"
                        " - Blowjob\n"
                        " - Threesome\n"
                        " - Toy play\n"
                        " - Intense orgasms 💦\n\n"
                        "🎁 90-day subscribers (R$59,90) enter a weekly draw for a video call with me!\n\n"
                        "🎥 Lifetime plan subscribers (R$119,90) enter a monthly draw to direct a full shoot with me 😏",
        "pix_msg": "🔑 Use the QR Code below or copy and paste the Pix code into your bank app:",
        "pix_erro": "Sorry, there was an error generating the payment. Please try again later."
    }
}

idioma_user = {}

# =====================
# PIX
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
        "payer": {"email": "cliente@teste.com"}
    }

    r = requests.post(url, headers=headers, json=data)

    if r.status_code == 201:
        j = r.json()
        return j["id"], j["point_of_interaction"]["transaction_data"]["qr_code"]

    return None, None

def gerar_qr(pix):
    img = qrcode.make(pix)
    bio = BytesIO()
    img.save(bio, "PNG")
    bio.seek(0)
    return bio

def consultar(payment_id):
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
# FLUXO (mantido igual)
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇧🇷 Português", callback_data="pt"))
    markup.add(types.InlineKeyboardButton("🇺🇸 English", callback_data="en"))
    markup.add(types.InlineKeyboardButton("🇪🇸 Español", callback_data="es"))

    bot.send_message(message.chat.id, "Escolha seu idioma / Choose your language / Elige tu idioma:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["pt","en","es"])
def idioma(call):
    chat_id = call.message.chat.id
    lang = call.data
    idioma_user[chat_id] = lang

    bot.send_message(chat_id, mensagens[lang]["inicio"])

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(mensagens[lang]["botao_inicio"], callback_data="ajuda"))

    try:
        video_path = os.path.join(os.path.dirname(__file__), "midia", "video01.mp4")

        if os.path.exists(video_path):
            with open(video_path, "rb") as video:
                bot.send_video(chat_id, video, caption=mensagens[lang]["video_caption"], reply_markup=markup)
    except Exception as e:
        print("ERRO VIDEO:", e)

@bot.callback_query_handler(func=lambda call: call.data == "ajuda")
def ajuda(call):
    chat_id = call.message.chat.id
    lang = idioma_user.get(chat_id, "pt")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(mensagens[lang]["botao_chave"], callback_data="planos"))

    bot.send_message(chat_id, mensagens[lang]["msg1"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "planos")
def planos(call):
    chat_id = call.message.chat.id
    lang = idioma_user.get(chat_id, "pt")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("7 dias - R$19,90", callback_data="30"))
    markup.add(types.InlineKeyboardButton("30 dias - R$29,90", callback_data="30"))
    markup.add(types.InlineKeyboardButton("90 dias - R$59,90", callback_data="90"))
    markup.add(types.InlineKeyboardButton("Vitalício - R$119,90", callback_data="vitalicio"))

    bot.send_message(chat_id, mensagens[lang]["planos_texto"], reply_markup=markup)

# =====================
# PAGAMENTO
# =====================
@bot.callback_query_handler(func=lambda call: call.data in ["7","30","90","vitalicio"])
def pagar(call):
    cur = get_cursor()
    chat_id = call.message.chat.id
    plano = call.data

    cur.execute("SELECT id, status, qr_enviado FROM pagamentos WHERE user_id=? AND status='pending'", (chat_id,))
    existente = cur.fetchone()

    if existente:
        if existente[2]:
            return
        pid = existente[0]
    else:
        pid = None

    valor = 19,90 if plano == "7" valor = 29,90 if plano == "30" else 59,90 if plano == "90" else 119,90

    payment_id, pix = criar_pix(valor)

    if not pix:
        bot.send_message(chat_id, mensagens[idioma_user.get(chat_id,"pt")]["pix_erro"])
        return

    lang = idioma_user.get(chat_id, "pt")

    if not pid:
        cur.execute("""
            INSERT INTO pagamentos (user_id, plano, payment_id, status, criado_em, qr_enviado)
            VALUES (?, ?, ?, 'pending', ?, 1)
        """, (chat_id, plano, payment_id, datetime.now().isoformat()))
    else:
        cur.execute("UPDATE pagamentos SET qr_enviado=1 WHERE id=?", (pid,))

    conn.commit()

    qr = gerar_qr(pix)

    bot.send_message(chat_id, mensagens[lang]["pix_msg"])
    bot.send_photo(chat_id, qr)
    bot.send_message(chat_id, pix)

# =====================
# LIBERAÇÃO
# =====================
def verificar():
    while True:
        try:
            cur = get_cursor()
            cur.execute("SELECT id, user_id, plano, payment_id FROM pagamentos WHERE status='pending'")
            dados = cur.fetchall()

            for pid, user_id, plano, payment_id in dados:
                status = consultar(payment_id)

                if status == "approved":
                    agora = datetime.now()

                    if plano == "7":
                        vence = agora + timedelta(days=7)
                    if plano == "30":
                        vence = agora + timedelta(days=30)
                    elif plano == "90":
                        vence = agora + timedelta(days=90)
                    else:
                        vence = None

                    cur.execute("UPDATE pagamentos SET status='approved', vence_em=? WHERE id=?",
                                (vence.isoformat() if vence else None, pid))
                    conn.commit()

                    link = bot.create_chat_invite_link(VIP_GROUP_ID, member_limit=1)
                    bot.send_message(user_id, f"🔥 Pagamento aprovado!\n\nAcesse:\n{link.invite_link}")

        except Exception as e:
            print("ERRO LIBERAÇÃO:", e)

        time.sleep(15)

# =====================
# REMOÇÃO
# =====================
def remover():
    while True:
        try:
            cur = get_cursor()
            agora = datetime.now().isoformat()

            cur.execute("""
                SELECT id, user_id FROM pagamentos
                WHERE status='approved'
                AND removido=0
                AND vence_em IS NOT NULL
                AND vence_em < ?
            """, (agora,))

            users = cur.fetchall()

            for pid, user_id in users:
                try:
                    bot.ban_chat_member(VIP_GROUP_ID, user_id)
                    bot.unban_chat_member(VIP_GROUP_ID, user_id)

                    cur.execute("UPDATE pagamentos SET removido=1 WHERE id=?", (pid,))
                    conn.commit()

                except Exception as e:
                    print("ERRO AO REMOVER:", e)

        except Exception as e:
            print("ERRO REMOÇÃO:", e)

        time.sleep(60)

# THREADS
threading.Thread(target=verificar, daemon=True).start()
threading.Thread(target=remover, daemon=True).start()

# =====================
# POLLING BLINDADO
# =====================
while True:
    try:
        print("Bot rodando...")
        bot.infinity_polling(timeout=30, long_polling_timeout=10, skip_pending=True)
    except Exception as e:
        print("RESTART:", e)
        time.sleep(5)
