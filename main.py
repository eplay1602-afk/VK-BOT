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

# 🧠 роли пользователей
roles = {}

# 🔐 кастомные права (user_id: [cmds])
permissions = {}

# ⏳ муты
mutes = {}

# 🧠 антиспам
spam = {}

# 🏷 кастомные названия ролей
role_names = {
    "mod": "Модератор",
    "admin": "Администратор",
    "user": "Пользователь"
}

def send(peer_id, text):
    vk.messages.send(
        peer_id=peer_id,
        message=text,
        random_id=int(time.time() * 1000)
    )

def is_admin(user_id):
    return user_id in ADMINS

def get_role(user_id):
    return roles.get(user_id, "user")

def has_perm(user_id, cmd):
    if is_admin(user_id):
        return True
    return cmd in permissions.get(user_id, [])

print("🚀 PRO MOD SYSTEM STARTED")

for event in longpoll.listen():

    if event.type != VkBotEventType.MESSAGE_NEW:
        continue

    msg = event.object.message
    text = msg.get("text", "")
    peer_id = msg.get("peer_id")
    user_id = msg.get("from_id")
    conv_id = msg.get("conversation_message_id")

    role = get_role(user_id)

    # ========================
    # ПРИВЕТСТВИЕ
    # ========================
    if event.from_chat and text == "":
        send(peer_id,
             "🔥 Спасибо что добавили меня в чат, пожалуйста выдайте звездочку для полной работы")

    # ========================
    # МУТ ПРОВЕРКА
    # ========================
    if user_id in mutes and mutes[user_id] > time.time():
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

    spam.setdefault(user_id, [])
    spam[user_id].append(now)
    spam[user_id] = [t for t in spam[user_id] if now - t < 3]

    if len(spam[user_id]) > 5:
        mutes[user_id] = now + 60
        send(peer_id, "⛔ Антиспам → мут 60 сек")
        continue

    # ========================
    # HELP (РАЗДЕЛЫ)
    # ========================
    if text == "/help":

        send(peer_id,
             "📌 КОМАНДЫ ПОЛЬЗОВАТЕЛЯ:\n"
             "/help\n"
             "— базовые команды\n\n"

             "🛡 МОДЕРАЦИЯ:\n"
             "/mute id sec\n"
             "/unmute id\n"
             "/pin\n\n"

             "👮 АДМИН:\n"
             "/ban id\n"
             "/givecmd id cmd\n"
             "/editroles role new_name\n"
        )

    # ========================
    # PIN
    # ========================
    if text.startswith("/pin") and has_perm(user_id, "pin"):
        try:
            vk.messages.pin(
                peer_id=peer_id,
                conversation_message_id=conv_id
            )
            send(peer_id, "📌 закреплено")
        except:
            send(peer_id, "ошибка pin")

    # ========================
    # BAN
    # ========================
    if text.startswith("/ban") and has_perm(user_id, "ban"):
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

    # ========================
    # MUTE
    # ========================
    if text.startswith("/mute") and has_perm(user_id, "mute"):
        try:
            parts = text.split()
            target = int(parts[1])
            sec = int(parts[2])

            mutes[target] = time.time() + sec
            send(peer_id, f"⏳ мут {target} на {sec} сек")
        except:
            send(peer_id, "формат: /mute id sec")

    # ========================
    # UNMUTE
    # ========================
    if text.startswith("/unmute") and has_perm(user_id, "mute"):
        try:
            target = int(text.split()[1])
            mutes.pop(target, None)
            send(peer_id, f"✅ мут снят")
        except:
            send(peer_id, "формат: /unmute id")

    # ========================
    # GIVE CMD (выдать доступ к команде)
    # ========================
    if text.startswith("/givecmd") and is_admin(user_id):
        try:
            _, target, cmd = text.split()

            target = int(target)

            permissions.setdefault(target, [])
            if cmd not in permissions[target]:
                permissions[target].append(cmd)

            send(peer_id, f"✅ выдан доступ: {cmd} → {target}")
        except:
            send(peer_id, "формат: /givecmd id cmd")

    # ========================
    # EDIT ROLES
    # ========================
    if text.startswith("/editroles") and is_admin(user_id):
        try:
            _, role, new_name = text.split(maxsplit=2)

            role_names[role] = new_name

            send(peer_id, f"🏷 роль {role} теперь '{new_name}'")
        except:
            send(peer_id, "формат: /editroles role name")