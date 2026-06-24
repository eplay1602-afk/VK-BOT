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

# ======================
# ADMINS + OWNER
# ======================
OWNER = 786886188
ADMINS = [786886188, 1092169800]

# ======================
# DATA STORAGE (RAM)
# ======================
roles = {}
role_names = {"admin": "Админ", "mod": "Модератор", "user": "Пользователь"}

nicks = {}
warns = {}
permissions = {}

# ======================
# SEND
# ======================
def send(peer_id, text):
    vk.messages.send(
        peer_id=peer_id,
        message=text,
        random_id=int(time.time() * 1000)
    )

def is_admin(uid):
    return uid in ADMINS

# ======================
# GET USER (reply/id/@)
# ======================
def resolve_user(text, reply=None):
    if reply:
        return reply

    if not text:
        return None

    m = re.search(r"id(\d+)", text)
    if m:
        return int(m.group(1))

    if text.isdigit():
        return int(text)

    try:
        res = vk.utils.resolveScreenName(screen_name=text.replace("@",""))
        if res and "object_id" in res:
            return res["object_id"]
    except:
        pass

    return None

def get_reply(event):
    msg = event.object.message
    r = msg.get("reply_message")
    return r.get("from_id") if r else None

# ======================
# HELP
# ======================
def help_text():
    return (
        "📌 КОМАНДЫ:\n\n"
        "👤 USER:\n"
        "/nlist\n"
        "/snick name (reply)\n"
        "/rnick (reply)\n\n"
        "🛡 MOD:\n"
        "/warn (reply)\n"
        "/pin (reply)\n"
        "/mute sec (reply)\n"
        "/unmute (reply)\n\n"
        "👮 ADMIN:\n"
        "/staff\n"
        "/roles\n"
        "/srole id role\n"
        "/rnroles role\n"
        "/givecmd id cmd\n"
        "/zov"
    )

# ======================
# MAIN
# ======================
print("🚀 FULL PRO BOT STARTED")

for event in longpoll.listen():

    if event.type != VkBotEventType.MESSAGE_NEW:
        continue

    msg = event.object.message
    text = msg.get("text", "")
    peer_id = msg.get("peer_id")
    user_id = msg.get("from_id")
    conv_id = msg.get("conversation_message_id")

    # ======================
    # HELP
    # ======================
    if text == "/help":
        send(peer_id, help_text())

    # ======================
    # STAFF
    # ======================
    if text == "/staff":
        admins = "\n".join([str(x) for x in ADMINS])
        send(peer_id, "👮 STAFF:\n" + admins)

    # ======================
    # ROLES LIST
    # ======================
    if text == "/roles":
        send(peer_id, "🏷 Роли:\n" + str(role_names))

    # ======================
    # SET ROLE
    # ======================
    if text.startswith("/srole") and is_admin(user_id):
        try:
            _, uid, role = text.split()
            roles[int(uid)] = role
            send(peer_id, "✅ роль выдана")
        except:
            send(peer_id, "формат: /srole id role")

    # ======================
    # REMOVE ROLE
    # ======================
    if text.startswith("/rnroles") and is_admin(user_id):
        try:
            role = text.split()[1]
            if role in role_names:
                del role_names[role]
                send(peer_id, "❌ роль удалена")
        except:
            send(peer_id, "формат: /rnroles role")

    # ======================
    # NEW ROLE
    # ======================
    if text.startswith("/srole") and is_admin(user_id):
        pass

    # ======================
    # WARN SYSTEM
    # ======================
    if text.startswith("/warn") and is_admin(user_id):
        target = get_reply(event)
        if not target:
            send(peer_id, "reply нужен")
        else:
            warns[target] = warns.get(target, 0) + 1
            send(peer_id, f"⚠️ warn +1 ({warns[target]}/3)")

            if warns[target] >= 3:
                send(peer_id, f"🚫 пользователь забанен (3 варна)")
                vk.groups.banUser(
                    group_id=GROUP_ID,
                    user_id=target,
                    end_date=0
                )

    # ======================
    # NICK SET
    # ======================
    if text.startswith("/snick"):
        target = get_reply(event)
        name = text.replace("/snick", "").strip()

        if target:
            nicks[target] = name
            send(peer_id, "✅ ник установлен")

    # ======================
    # REMOVE NICK
    # ======================
    if text == "/rnick":
        target = get_reply(event)
        if target and target in nicks:
            del nicks[target]
            send(peer_id, "❌ ник удалён")

    # ======================
    # NICK LIST
    # ======================
    if text == "/nlist":
        send(peer_id, str(nicks))

    # ======================
    # ZOV (ping all)
    # ======================
    if text == "/zov":
        try:
            members = vk.messages.getConversationMembers(peer_id=peer_id)
            users = members.get("profiles", [])

            mentions = []
            for u in users:
                mentions.append(f"@id{u['id']}")

            send(peer_id, "📣 " + " ".join(mentions))
        except:
            send(peer_id, "ошибка zov")

    # ======================
    # PIN
    # ======================
    if text == "/pin" and is_admin(user_id):
        try:
            vk.messages.pin(peer_id=peer_id, conversation_message_id=conv_id)
            send(peer_id, "📌 закреплено")
        except:
            send(peer_id, "error pin")