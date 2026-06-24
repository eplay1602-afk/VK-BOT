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
OWNER = 786886188

roles = {}        # user_id -> role
role_priority = { # роль -> приоритет
    "owner": 100,
    "admin": 80,
    "mod": 50,
    "user": 10
}

nicks = {}
warns = {}

# ========================
# VK USER INFO (NAME SYSTEM)
# ========================
def get_user_info(user_id):
    try:
        u = vk.users.get(user_ids=user_id)[0]
        return f"{u['first_name']} {u['last_name']} (@id{user_id})"
    except:
        return f"Unknown (@id{user_id})"

# ========================
# SEND
# ========================
def send(peer_id, text):
    vk.messages.send(
        peer_id=peer_id,
        message=text,
        random_id=int(time.time() * 1000)
    )

# ========================
# REPLY USER
# ========================
def get_reply(event):
    msg = event.object.message
    r = msg.get("reply_message")
    return r.get("from_id") if r else None

# ========================
# RESOLVE USER
# ========================
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
        r = vk.utils.resolveScreenName(screen_name=text.replace("@",""))
        if r and "object_id" in r:
            return r["object_id"]
    except:
        pass

    return None

# ========================
# HELP
# ========================
def help_text():
    return (
        "📌 КОМАНДЫ:\n\n"
        "🛡 MODERATION:\n"
        "/warn (reply)\n"
        "/pin (reply)\n\n"
        "👤 USER:\n"
        "/snick text (reply)\n"
        "/rnick (reply)\n"
        "/nlist\n\n"
        "👮 ADMIN:\n"
        "/staff\n"
        "/roles\n"
        "/zov"
    )

print("🚀 FORMAT PRO BOT STARTED")

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
    # HELP
    # ========================
    if text == "/help":
        send(peer_id, help_text())

    # ========================
    # STAFF (FULL NAME + ROLE)
    # ========================
    if text == "/staff":
        lines = []
        for uid in ADMINS:
            name = get_user_info(uid)
            role = "OWNER" if uid == OWNER else "ADMIN"
            lines.append(f"{name} — {role}")

        send(peer_id, "👮 STAFF:\n" + "\n".join(lines))

    # ========================
    # ROLES (name - priority)
    # ========================
    if text == "/roles":
        lines = []
        for r, p in role_priority.items():
            lines.append(f"{r} — приоритет {p}")

        send(peer_id, "🏷 РОЛИ:\n" + "\n".join(lines))

    # ========================
    # NICK SET
    # ========================
    if text.startswith("/snick"):
        target = get_reply(event)
        nick = text.replace("/snick", "").strip()

        if target:
            nicks[target] = nick
            send(peer_id, "✅ ник установлен")

    # ========================
    # NICK LIST (NAME + NICK)
    # ========================
    if text == "/nlist":
        lines = []
        for uid, nick in nicks.items():
            name = get_user_info(uid)
            lines.append(f"{name} — Ник: \"{nick}\"")

        send(peer_id, "\n".join(lines) if lines else "пусто")

    # ========================
    # REMOVE NICK
    # ========================
    if text == "/rnick":
        target = get_reply(event)
        if target and target in nicks:
            del nicks[target]
            send(peer_id, "❌ ник удалён")

    # ========================
    # ZOV (ALL USERS)
    # ========================
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

    # ========================
    # PIN
    # ========================
    if text == "/pin":
        try:
            vk.messages.pin(peer_id=peer_id, conversation_message_id=conv_id)
            send(peer_id, "📌 закреплено")
        except:
            send(peer_id, "error pin")