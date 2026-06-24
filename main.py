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
# SEND
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
# RESOLVE @username -> id
# ========================
def resolve_user(name):
    try:
        if not name:
            return None

        name = name.replace("@", "")

        res = vk.utils.resolveScreenName(screen_name=name)

        if res and "object_id" in res:
            return res["object_id"]

    except:
        pass

    return None

# ========================
# GET REPLY USER
# ========================
def get_reply_user(event):
    msg = event.object.message
    reply = msg.get("reply_message")
    if reply:
        return reply.get("from_id")
    return None

# ========================
# EXTRACT USER
# ========================
def get_user(text_part, reply_user=None):

    if reply_user:
        return reply_user

    if not text_part:
        return None

    # id123
    m = re.search(r"id(\d+)", text_part)
    if m:
        return int(m.group(1))

    # 123456
    if text_part.isdigit():
        return int(text_part)

    # @username
    return resolve_user(text_part)

# ========================
# MAIN
# ========================
print("🚀 FIXED PRO BOT STARTED")

for event in longpoll.listen():

    if event.type != VkBotEventType.MESSAGE_NEW:
        continue

    msg = event.object.message
    text = msg.get("text", "")
    peer_id = msg.get("peer_id")
    user_id = msg.get("from_id")
    conv_id = msg.get("conversation_message_id")

    now = time.time()

    # ========================
    # SPAM
    # ========================
    spam.setdefault(user_id, [])
    spam[user_id].append(now)
    spam[user_id] = [t for t in spam[user_id] if now - t < 3]

    if len(spam[user_id]) > 5:
        mutes[user_id] = now + 60
        send(peer_id, "⛔ мут 60 сек (антиспам)")
        continue

    # ========================
    # PIN (reply)
    # ========================
    if text.startswith("/pin") and is_admin(user_id):
        try:
            vk.messages.pin(
                peer_id=peer_id,
                conversation_message_id=conv_id
            )
            send(peer_id, "📌 закреплено")
        except:
            send(peer_id, "ошибка pin")

    # ========================
    # MUTE (reply / id / @username)
    # ========================
    if text.startswith("/mute") and is_admin(user_id):
        try:
            parts = text.split()

            sec = int(parts[1])

            reply_user = get_reply_user(event)

            target_text = parts[2] if len(parts) > 2 else ""
            target = get_user(target_text, reply_user)

            if not target:
                send(peer_id, "❌ не найден пользователь (reply / id / @username)")
            else:
                mutes[target] = now + sec
                send(peer_id, f"⏳ мут {target} на {sec} сек")

        except:
            send(peer_id, "формат: /mute 120 (reply / id / @user)")

    # ========================
    # UNMUTE
    # ========================
    if text.startswith("/unmute") and is_admin(user_id):
        try:
            parts = text.split()
            reply_user = get_reply_user(event)

            target_text = parts[1] if len(parts) > 1 else ""
            target = get_user(target_text, reply_user)

            if not target:
                send(peer_id, "❌ не найден пользователь")
            else:
                mutes.pop(target, None)
                send(peer_id, f"✅ мут снят {target}")

        except:
            send(peer_id, "формат: /unmute (reply / id / @user)")

    # ========================
    # HELP
    # ========================
    if text == "/help":
        send(peer_id,
             "📌 КОМАНДЫ:\n\n"
             "🛡 модерация:\n"
             "/pin (reply)\n"
             "/mute 120 (reply / id / @user)\n"
             "/unmute (reply / id / @user)\n"
        )