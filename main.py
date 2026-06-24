import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import os
import time

TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

# 🔐 список админов (впиши свой VK ID)
ADMINS = [123456789]

def send(peer_id, text):
    vk.messages.send(
        peer_id=peer_id,
        message=text,
        random_id=int(time.time() * 1000)
    )

def is_admin(user_id):
    return user_id in ADMINS

print("🚀 MOD BOT STARTED")

for event in longpoll.listen():
    print("EVENT:", event.type)

    # ========================
    # НОВОЕ СООБЩЕНИЕ
    # ========================
    if event.type == VkBotEventType.MESSAGE_NEW:
        msg = event.object.message

        text = msg.get("text", "")
        peer_id = msg.get("peer_id")
        user_id = msg.get("from_id")

        # ========================
        # ПРИВЕТСТВИЕ В БЕСЕДЕ
        # ========================
        if event.from_chat:
            if text == "":
                send(peer_id,
                     "🔥 Спасибо что добавили меня в чат, пожалуйста выдайте звездочку для полной работы")

        # ========================
        # КОМАНДЫ МОДЕРАЦИИ
        # ========================

        # /pin
        if text.startswith("/pin"):
            if is_admin(user_id):
                try:
                    msg_id = msg["conversation_message_id"]

                    vk.messages.pin(
                        peer_id=peer_id,
                        conversation_message_id=msg_id
                    )

                    send(peer_id, "📌 Сообщение закреплено")
                except Exception as e:
                    send(peer_id, f"Ошибка pin: {e}")
            else:
                send(peer_id, "⛔ нет доступа")

        # /ban
        if text.startswith("/ban"):
            if is_admin(user_id):
                try:
                    args = text.split()
                    target_id = int(args[1])

                    vk.groups.banUser(
                        group_id=GROUP_ID,
                        user_id=target_id,
                        end_date=0
                    )

                    send(peer_id, f"🚫 Пользователь {target_id} забанен")
                except:
                    send(peer_id, "Используй: /ban id")
            else:
                send(peer_id, "⛔ нет доступа")

        # /mute (простая версия — просто сообщение)
        if text.startswith("/mute"):
            if is_admin(user_id):
                send(peer_id, "⏳ мут система будет добавлена (следующий апгрейд)")
            else:
                send(peer_id, "⛔ нет доступа")

        # /help
        if text == "/help":
            send(peer_id,
                 "📋 Команды:\n"
                 "/pin — закрепить\n"
                 "/ban id — бан\n"
                 "/help — помощь")