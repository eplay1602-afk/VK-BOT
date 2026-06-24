import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import os
import time
import re
import pymysql


TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

ADMINS = [786886188, 1092169800]
OWNER = 786886188


# ========================
# MYSQL
# ========================
db = pymysql.connect(
    host="127.0.0.1",
    user="whg115198_",
    password="Perm_323",
    database="whg115198_",
    port=3306,
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)

def q(sql, args=None):
    with db.cursor() as cur:
        cur.execute(sql, args or ())
        return cur.fetchall()


# ========================
# VK USER INFO
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
        r = vk.utils.resolveScreenName(screen_name=text.replace("@", ""))
        if r and "object_id" in r:
            return r["object_id"]
    except:
        pass

    return None


# ========================
# ROLE SYSTEM (DB)
# ========================
def get_role(user_id):
    r = q("SELECT role FROM users WHERE user_id=%s", (user_id,))
    return r[0]["role"] if r else "user"


# ========================
# NICK SYSTEM (DB)
# ========================
def set_nick(user_id, nick):
    q("""
        INSERT INTO nicks (user_id, nick)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE nick=%s
    """, (user_id, nick, nick))


def get_nick(user_id):
    r = q("SELECT nick FROM nicks WHERE user_id=%s", (user_id,))
    return r[0]["nick"] if r else None


def remove_nick(user_id):
    q("DELETE FROM nicks WHERE user_id=%s", (user_id,))


# ========================
# GREETING SYSTEM
# ========================
def set_greeting(peer_id, text):
    q("""
        INSERT INTO greetings (peer_id, text)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE text=%s
    """, (peer_id, text, text))


def get_greeting(peer_id):
    r = q("SELECT text FROM greetings WHERE peer_id=%s", (peer_id,))
    return r[0]["text"] if r else None


def remove_greeting(peer_id):
    q("DELETE FROM greetings WHERE peer_id=%s", (peer_id,))


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
        "/nlist\n"
        "/hi текст\n"
        "/rhi\n\n"
        "👮 ADMIN:\n"
        "/staff\n"
        "/roles\n"
        "/zov"
    )


print("🚀 BOT STARTED")


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
    # AUTO GREETING
    # ========================
    g = get_greeting(peer_id)
    if g:
        send(peer_id, g.replace("{user}", get_user_info(user_id)))

    # ========================
    # HELP
    # ========================
    if text == "/help":
        send(peer_id, help_text())

    # ========================
    # STAFF
    # ========================
    if text == "/staff":
        lines = []
        for uid in ADMINS:
            name = get_user_info(uid)
            role = "OWNER" if uid == OWNER else "ADMIN"
            lines.append(f"{name} — {role}")

        send(peer_id, "👮 STAFF:\n" + "\n".join(lines))

    # ========================
    # ROLES
    # ========================
    if text == "/roles":
        send(peer_id, "owner — 100\nadmin — 80\nmod — 50\nuser — 10")

    # ========================
    # SNICK
    # ========================
    if text.startswith("/snick"):
        target = get_reply(event)
        nick = text.replace("/snick", "").strip()

        if target and nick:
            set_nick(target, nick)
            send(peer_id, "✅ ник установлен")

    # ========================
    # NICK LIST
    # ========================
    if text == "/nlist":
        rows = q("SELECT * FROM nicks")

        if not rows:
            send(peer_id, "пусто")
        else:
            lines = []
            for r in rows:
                uid = r["user_id"]
                nick = r["nick"]
                name = get_user_info(uid)
                lines.append(f"{name} — Ник: \"{nick}\"")

            send(peer_id, "\n".join(lines))

    # ========================
    # REMOVE NICK
    # ========================
    if text == "/rnick":
        target = get_reply(event)
        if target:
            remove_nick(target)
            send(peer_id, "❌ ник удалён")

    # ========================
    # ZOV
    # ========================
    if text == "/zov":
        try:
            members = vk.messages.getConversationMembers(peer_id=peer_id)
            users = members.get("profiles", [])

            mentions = [f"@id{u['id']}" for u in users]
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

    # ========================
    # HI
    # ========================
    if text.startswith("/hi"):
        set_greeting(peer_id, text.replace("/hi", "").strip())
        send(peer_id, "✅ приветствие установлено")

    # ========================
    # RHI
    # ========================
    if text == "/rhi":
        remove_greeting(peer_id)
        send(peer_id, "❌ приветствие удалено")