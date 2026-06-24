import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import os

TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

print("🚀 BOT STARTED")
print("GROUP_ID =", GROUP_ID)

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

def send(peer_id, text):
    vk.messages.send(
        peer_id=peer_id,
        message=text,
        random_id=0
    )

for event in longpoll.listen():
    print("EVENT:", event.type)

    if event.type == VkBotEventType.MESSAGE_NEW:
        msg = event.object.message

        text = msg.get("text", "")
        peer_id = msg.get("peer_id")

        print("MESSAGE:", text, peer_id)

        # отвечает в беседах
        if peer_id > 2000000000:
            if text.lower() == "привет":
                send(peer_id, "Я подключен к чату 👮")