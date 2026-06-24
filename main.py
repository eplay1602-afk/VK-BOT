import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import os

TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

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
    if event.type == VkBotEventType.MESSAGE_NEW:
        msg = event.object.message
        text = msg["text"].lower()
        peer_id = msg["peer_id"]

        if text == "привет":
            send(peer_id, "Я живой модератор-бот 👮")
