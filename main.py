import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import os
import time

TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

ADMINS = [786886188, 1092169800]

mutes = {}
spam = {}

def send(peer_id, text):
    vk.messages.send(
        peer_id=peer_id,
        message=text,
        random_id=int(time.time() * 1000)
    )

def is_admin(user_id):
    return user_id in ADMINS

def extract_reply(event):
    msg = event.object.message

    # ID сообщения на которое ответили
    fwd = msg.get("reply_message")

    if fwd:
        return fwd.get("from_id")
    return None

print("🚀 PRO MOD BOT WITH REPLY STARTED")

for event in longpoll.listen():

    if event.type != VkBotEventType.MESSAGE_NEW:
        continue

    msg = event.object.message
    text = msg.get("text", "")
    peer_id = msg.get("peer_id")
    user_id = msg.get("from_id")
    conv_id = msg.get("conversation_message_id")

    # ========================
    # ANTI SPAM (простая)
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
    # /PIN (reply)
    # ========================
    if text.startswith("/pin") and is_admin(user_id):
        try:
            vk.messages.pin(
                peer_id=peer_id,
                conversation_message_id=conv_id
            )
            send(peer_id, "📌 Закреплено сообщение (reply)")
        except:
            send(peer_id, "ошибка pin")

    # ========================
    # /MUTE (reply)
    # ========================
    if text.startswith("/mute") and is_admin(user_id):
        try:
            parts = text.split()
            sec = int(parts[1])

            target = extract_reply(event)

            if not target:
                send(peer_id, "❌ Сделай reply на сообщение пользователя")
            else:
                mutes[target] = time.time() + sec
                send(peer_id, f"⏳ мут {target} на {sec} сек")

        except:
            send(peer_id, "формат: /mute 120 (reply)")

    # ========================
    # /BAN (reply)
    # ========================
    if text.startswith("/ban") and is_admin(user_id):
        try:
            target = extract_reply(event)

            if not target:
                send(peer_id, "❌ сделай reply на пользователя")
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
    # /HELP
    # ========================
    if text == "/help":
        send(peer_id,
             "📌 КОМАНДЫ:\n\n"
             "👤 Пользователь:\n"
             "/help\n\n"
             "🛡 Модерация (reply):\n"
             "/mute 120 (reply)\n"
             "/ban (reply)\n"
             "/pin (reply)\n\n"
             "👮 Админ:\n"
             "все команды выше + доступ")