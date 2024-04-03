import telebot
import threading
import sqlite3
import traceback

bot = telebot.TeleBot('7160523558:AAHj8zEab0NQlzoxnovapdkqKWEgApCzUek')

DEV_ID = 5139305942
GROUP_ID = -4096459398
ADMIN_ID = 6384028168

lock = threading.Lock()

saldear_requests = {}

conn = sqlite3.connect('tokens.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS tokens
             (id INTEGER PRIMARY KEY, user_id TEXT UNIQUE, tokens INTEGER)''')
conn.commit()

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Este es un bot de saldeo de ccs.\n"
                          "Dueño del bot: @NGCDADD1\n"
                          "Dev: @Neweazye")

@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.reply_to(message, "Comandos:\n"
                          "/saldear <16 digitos> Ejemplo: /saldear 1234567891234567\n"
                          "Este comando saldeará tu cc.\n"
                          "/me\n"
                          "Este comando te dirá tu información en el bot, mostrando la cantidad de tokens que quedan.")

@bot.message_handler(commands=['saldeador'])
def handle_saldeador(message):
    if message.chat.id == GROUP_ID:
        bot.reply_to(message, "Este mensaje solo aparece en el grupo de saldeadores.\n"
                              "Por favor, para responder al mensaje haga el siguiente formato:\n"
                              "/saldo (16 digitos) 1 Pago: (cantidad de 1 pago) / Cuotas: (Cantidad en cuotas)\n"
                              "Ejemplo de formato (para poder responder al bot vea el siguiente ejemplo):\n"
                              "/saldo 1234567891234567 1 Pago: $467.140,42 / Cuotas: $467.465,42\n"
                              "Para los 16 digitos puede copiar y pegar el mensaje para mayor seguridad, "
                              "si los 16 digitos están mal, el cliente no podrá ver el mensaje.\n"
                              "Dudas? @Neweazye")
    else:
        bot.reply_to(message, "Este comando solo puede ser utilizado en el grupo de saldeadores.")

@bot.message_handler(commands=['saldear'])
def handle_saldear(message):
    user_id = message.chat.id
    tokens = get_tokens(user_id)
    if tokens <= 0:
        bot.reply_to(message, f"Lo siento, no tienes tokens de saldeo. Comunícate con @NGCDADD1 para obtenerlos.")
        return
    consume_token(user_id)
    try:
        digits = message.text.split(maxsplit=1)[1].strip()
        if len(digits) != 16 or not digits.isdigit():
            bot.reply_to(message, "Por favor, ingresa los 16 dígitos numéricos de la cc.")
            return
    except IndexError:
        bot.reply_to(message, "Por favor, ingresa 16 dígitos numéricos válidos.")
        return
    saldear_requests[user_id] = {'digits': digits}
    bot.send_message(GROUP_ID, f"Cliente {user_id} desea saldear: {digits}\n")
    bot.reply_to(message, "Tu solicitud de saldeo ha sido registrada.")

@bot.message_handler(commands=['saldo'])
def handle_saldo(message):
    if message.chat.id == GROUP_ID:
        user_id_and_digits, rest_of_message = message.text.split(maxsplit=1)[1].split(maxsplit=1)
        digits = user_id_and_digits[:16]
        original_message = f"Respuesta al mensaje: {digits} {rest_of_message}"
        for user_id, data in saldear_requests.items():
            if data['digits'] == digits:
                bot.send_message(user_id, original_message)
                del saldear_requests[user_id]
                break

@bot.message_handler(commands=['add'])
def handle_add(message):
    if message.from_user.id == ADMIN_ID:
        try:
            parts = message.text.split()
            user_id = parts[1]
            tokens = int(parts[2])
            with lock:
                c.execute("INSERT OR IGNORE INTO tokens (user_id, tokens) VALUES (?, ?)", (user_id, tokens))
                c.execute("UPDATE tokens SET tokens = tokens + ? WHERE user_id = ?", (tokens, user_id))
                conn.commit()
            bot.reply_to(message, f"Se han agregado {tokens} tokens al usuario {user_id}.")
        except Exception as e:
            print(e)
            bot.reply_to(message, "Ocurrió un error al agregar tokens.")
    else:
        bot.reply_to(message, "Este comando solo puede ser utilizado por el dueño del bot.")

def get_tokens(user_id):
    with lock:
        c.execute("SELECT tokens FROM tokens WHERE user_id=?", (str(user_id),))
        result = c.fetchone()
        if result:
            return result[0]
        else:
            return 0

def consume_token(user_id):
    with lock:
        c.execute("UPDATE tokens SET tokens=tokens-1 WHERE user_id=?", (str(user_id),))
        conn.commit()

@bot.message_handler(commands=['me'])
def handle_me(message):
    user_id = message.from_user.id
    registered = is_registered(user_id)
    tokens = get_tokens(user_id)
    response = f"Registrado en DB: {'Si' if registered else 'No'}\n"
    response += f"Id del usuario: {user_id}\n"
    response += f"Tokens restantes: {tokens}"
    bot.reply_to(message, response)

def error_handler(e):
    print(f"Se ha producido un error:\n{traceback.format_exc()}")
    bot.send_message(DEV_ID, f"Se ha producido un error:\n{str(e)}")

@bot.message_handler(commands=['info'])
def handle_info(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Este comando solo puede ser utilizado por el administrador.")
        return
    try:
        user_id = message.text.split()[1]
        tokens = get_tokens(user_id)
        bot.reply_to(message, f"Registrado en DB: Si\nId del usuario: {user_id}\nTokens restantes: {tokens}")
    except IndexError:
        bot.reply_to(message, "Por favor, proporciona el ID del usuario.")

def is_registered(user_id):
    with lock:
        c.execute("SELECT 1 FROM tokens WHERE user_id=?", (str(user_id),))
        return c.fetchone() is not None

def get_tokens(user_id):
    with lock:
        c.execute("SELECT tokens FROM tokens WHERE user_id=?", (str(user_id),))
        result = c.fetchone()
        if result:
            return result[0]
        else:
            return 0

bot.polling()
