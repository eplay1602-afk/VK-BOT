import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import os
import time
import re

TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

ADMINS = [786886188, 1092169800]

mutes = {}
spam = {}

# ========================
# УТИЛИТЫ
# ========================

def send(peer_id, text):
    vk.messages.send(
        peer_id=peer_id,
        message=text,
        random_id=int(time.time() * 1000)
    )

def is_admin(user_id):
    return user_id in ADMINS

# ========================
# ПАРСЕР USER ID (ID / @id / text)
# ========================
def extract_user_id(text, reply_user=None):

    if reply_user:
        return reply_user

    if not text:
        return None

    # id123456
    match = re.search(r"id(\d+)", text)
    if match:
        return int(match.group(1))

    # @id123456
    match = re.search(r"@id(\d+)", text)
    if match:
        return int(match.group(1))

    # чистое число
    if text.isdigit():
        return int(text)

    return None

# ========================
# REPLY USER ID
# ========================
def get_reply_user(event):
    msg = event.object.message
    reply = msg.get("reply_message")
    if reply:
        return reply.get("from_id")
    return None

print("🚀 PRO MOD BOT FULL STARTED")

# ========================
# MAIN LOOP
# ========================
for event in longpoll.listen():

    if event.type != VkBotEventType.MESSAGE_NEW:
        continue

    msg = event.object.message
    text = msg.get("text", "")
    peer_id = msg.get("peer_id")
    user_id = msg.get("from_id")
    conv_id = msg.get("conversation_message_id")

    # ========================
    # SPAM PROTECTION
    # ========================
    now = time.time()

    spam.setdefault(user_id, [])
    spam[user_id].append(now)
    spam[user_id] = [t for t in spam[user_id] if now - t < 3]

    if len(spam[user_id]) > 5:
        mutes[user_id] = now + 60
        send(peer_id, "⛔ Антиспам → мут 60 сек")
        continue

    # ========================
    # PIN (reply only)
    # ========================
    if text.startswith("/pin") and is_admin(user_id):
        try:
            vk.messages.pin(
                peer_id=peer_id,
                conversation_message_id=conv_id
            )
            send(peer_id, "📌 сообщение закреплено")
        except:
            send(peer_id, "ошибка pin")

    # ========================
    # MUTE (reply + id + @user)
    # ========================
    if text.startswith("/mute") and is_admin(user_id):
        try:
            parts = text.split()
            sec = int(parts[1]) if len(parts) > 1 else 0

            reply_user = get_reply_user(event)
            target = extract_user_id(parts[2] if len(parts) > 2 else "", reply_user)

            if not target:
                send(peer_id, "❌ укажи пользователя (reply / id / @id)")
            else:
                mutes[target] = time.time() + sec
                send(peer_id, f"⏳ мут {target} на {sec} сек")

        except:
            send(peer_id, "формат: /mute 120 (reply / id / @id)")

    # ========================
    # UNMUTE
    # ========================
    if text.startswith("/unmute") and is_admin(user_id):
        try:
            reply_user = get_reply_user(event)
            parts = text.split()

            target = extract_user_id(parts[1] if len(parts) > 1 else "", reply_user)

            if target in mutes:
                del mutes[target]
                send(peer_id, f"✅ мут снят {target}")
            else:
                send(peer_id, "пользователь не в муте")

        except:
            send(peer_id, "формат: /unmute (reply / id / @id)")

    # ========================
    # BAN
    # ========================
    if text.startswith("/ban") and is_admin(user_id):
        try:
            reply_user = get_reply_user(event)
            parts = text.split()

            target = extract_user_id(parts[1] if len(parts) > 1 else "", reply_user)

            if not target:
                send(peer_id, "❌ укажи пользователя")
            else:
                vk.groups.banUser(
                    group_id=GROUP_ID,
                    user_id=target,
                    end_date=0
                )
                send(peer_id, f"🚫 бан {target}")

        except:
            send(peer_id, "ошибка ban")

    # ========================
    # HELP
    # ========================
    if text == "/help":
        send(peer_id,
             "📌 КОМАНДЫ:\n\n"
             "👤 Пользователь:\n"
             "/help\n\n"
             "🛡 Модерация:\n"
             "/pin (reply)\n"
             "/mute 120 (reply / id / @user)\n"
             "/unmute (reply / id / @user)\n"
             "/ban (reply / id / @user)\n"
        )