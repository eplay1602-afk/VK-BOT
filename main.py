import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import os
import time

TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

# 👮 админы
ADMINS = [786886188, 1092169800]

# ⏳ муты
mutes = {}

# 🧠 антиспам
spam_memory = {}

def send(peer_id, text):
    vk.messages.send(
        peer_id=peer_id,
        message=text,
        random_id=int(time.time() * 1000)
    )

def is_admin(user_id):
    return user_id in ADMINS

def is_muted(user_id):
    return user_id in mutes and mutes[user_id] > time.time()

print("🚀 PRO MOD BOT STARTED")

for event in longpoll.listen():

    if event.type != VkBotEventType.MESSAGE_NEW:
        continue

    msg = event.object.message
    text = msg.get("text", "")
    peer_id = msg.get("peer_id")
    user_id = msg.get("from_id")
    conv_id = msg.get("conversation_message_id")

    # ========================
    # ПРИВЕТСТВИЕ В БЕСЕДЕ
    # ========================
    if event.from_chat:
        if text == "":
            send(peer_id,
                 "🔥 Спасибо что добавили меня в чат, пожалуйста выдайте звездочку для полной работы")

    # ========================
    # МУТ
    # ========================
    if is_muted(user_id):
        try:
            vk.messages.delete(
                message_ids=str(conv_id),
                delete_for_all=True
            )
        except:
            pass
        continue

    # ========================
    # АНТИСПАМ
    # ========================
    now = time.time()

    if user_id not in spam_memory:
        spam_memory[user_id] = []

    spam_memory[user_id].append(now)
    spam_memory[user_id] = [t for t in spam_memory[user_id] if now - t < 3]

    if len(spam_memory[user_id]) > 5:
        mutes[user_id] = now + 60
        send(peer_id, "⛔ Антиспам: мут на 60 сек")
        continue

    # ========================
    # КОМАНДЫ
    # ========================

    # /help
    if text == "/help":
        send(peer_id,
             "/pin — закреп\n"
             "/ban id — бан\n"
             "/mute id sec — мут\n"
             "/unmute id — снять мут")

    # /pin
    if text.startswith("/pin") and is_admin(user_id):
        try:
            vk.messages.pin(
                peer_id=peer_id,
                conversation_message_id=conv_id
            )
            send(peer_id, "📌 закреплено")
        except:
            send(peer_id, "ошибка pin")

    # /ban
    if text.startswith("/ban") and is_admin(user_id):
        try:
            target = int(text.split()[1])

            vk.groups.banUser(
                group_id=GROUP_ID,
                user_id=target,
                end_date=0
            )

            send(peer_id, f"🚫 бан {target}")
        except:
            send(peer_id, "формат: /ban id")

    # /mute
    if text.startswith("/mute") and is_admin(user_id):
        try:
            parts = text.split()
            target = int(parts[1])
            sec = int(parts[2])

            mutes[target] = time.time() + sec
            send(peer_id, f"⏳ мут {target} на {sec} сек")
        except:
            send(peer_id, "формат: /mute id sec")

    # /unmute
    if text.startswith("/unmute") and is_admin(user_id):
        try:
            target = int(text.split()[1])
            if target in mutes:
                del mutes[target]
            send(peer_id, f"✅ мут снят {target}")
        except:
            send(peer_id, "формат: /unmute id")